"""Cursor CLI adapter used by every Factory role.

Cursor has changed its executable name over time.  This module owns binary
discovery, capability and authentication checks, the non-interactive command
contract, and normalization of Cursor's JSON result envelope.  The rest of the
Factory never needs to know whether the installed executable is ``agent`` or
the compatibility name ``cursor-agent``.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

from adapter_capabilities import role_environment
from sensitive_data import redact_credentials


REQUIRED_OPTIONS = ("--print", "--output-format", "--force", "--mode", "--sandbox")
CURSOR_ENVIRONMENT = (
    "CURSOR_API_KEY",
    "CURSOR_CONFIG_DIR",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
    "FACTORY_CURSOR_BIN",
    "FACTORY_CURSOR_MODEL",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "NODE_EXTRA_CA_CERTS",
)


class CursorCLIError(RuntimeError):
    """Raised when the installed Cursor CLI cannot satisfy the adapter contract."""


def cursor_configuration_issue(cwd: Path) -> str:
    """Fail before model startup when undocumented isolation would be required.

    Cursor documents configuration inheritance but no per-run MCP exclusion flag.
    Do not edit personal settings or silently reuse an unrelated tool catalog.
    """
    root = cwd.resolve()
    candidates = {parent / ".cursor/mcp.json" for parent in (root, *root.parents)}
    candidates.add(Path.home() / ".cursor/mcp.json")
    if os.environ.get("CURSOR_CONFIG_DIR"):
        candidates.add(Path(os.environ["CURSOR_CONFIG_DIR"]) / "mcp.json")
    if os.environ.get("XDG_CONFIG_HOME"):
        candidates.add(Path(os.environ["XDG_CONFIG_HOME"]) / "cursor/mcp.json")
    for directory, children, files in os.walk(root) if (root / ".git").exists() else ():
        children[:] = [name for name in children if name not in {
            ".git", ".factory", "node_modules", ".venv", "venv", "dist", "build", ".next",
        }]
        if Path(directory).name == ".cursor" and "mcp.json" in files:
            candidates.add(Path(directory) / "mcp.json")
    for path in sorted(candidates):
        if not path.is_file():
            continue
        try:
            value = json.loads(path.read_text())
        except (ValueError, OSError):
            return f"Cursor MCP configuration cannot be checked: {path}. Fix its JSON before running the factory."
        if not isinstance(value, dict) or value.get("mcpServers"):
            return (
                f"Cursor MCP configuration detected at {path}. The supported CLI has no verified per-run MCP exclusion. "
                "Choose Claude or Codex in Setup, or use a separate Cursor environment without MCP servers and sign in there. "
                "The factory has not changed your personal settings."
            )
    return ""


def cursor_environment(*additional: str) -> dict[str, str]:
    """Return the bounded environment allowed to reach Cursor."""
    return role_environment(*CURSOR_ENVIRONMENT, *additional)


def cursor_candidates(
    environment: Mapping[str, str] | None = None,
) -> list[str]:
    """Return explicit, current, then compatibility Cursor executable candidates."""
    source = os.environ if environment is None else environment
    override = source.get("FACTORY_CURSOR_BIN", "").strip()
    search_path = source.get("PATH")
    candidates = [override] if override else [
        shutil.which("agent", path=search_path),
        shutil.which("cursor-agent", path=search_path),
    ]
    return list(dict.fromkeys(candidate for candidate in candidates if candidate))


def cursor_help_compatible(output: str) -> bool:
    """Check only flags the Factory relies on; ignore unrelated CLI additions."""
    return all(option in output for option in REQUIRED_OPTIONS)


def probe_cursor_cli(
    candidate: str,
    cwd: Path,
    *,
    timeout: int = 10,
) -> tuple[bool, str]:
    """Verify the local CLI contract and login without making a model request."""
    issue = cursor_configuration_issue(cwd)
    if issue:
        return False, issue
    environment = cursor_environment()
    try:
        help_result = subprocess.run(
            [candidate, "--help"], cwd=cwd, text=True, capture_output=True,
            timeout=timeout, env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    help_output = help_result.stdout + help_result.stderr
    if help_result.returncode or not cursor_help_compatible(help_output):
        missing = [option for option in REQUIRED_OPTIONS if option not in help_output]
        detail = ", ".join(missing) if missing else "help command failed"
        return False, (
            f"update Cursor CLI with `{candidate} update`; "
            f"required options missing: {detail}"
        )
    try:
        status = subprocess.run(
            [candidate, "status"], cwd=cwd, text=True, capture_output=True,
            timeout=timeout, env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if status.returncode:
        return False, "not signed in; run `agent login` or set CURSOR_API_KEY"
    return True, candidate


def resolve_cursor_cli(cwd: Path | None = None) -> str:
    """Resolve one authenticated Cursor CLI that supports the Factory contract."""
    root = (cwd or Path.cwd()).resolve()
    details: list[str] = []
    candidates = cursor_candidates()
    for candidate in candidates:
        ready, detail = probe_cursor_cli(candidate, root)
        if ready:
            return candidate
        details.append(detail)
    override = os.environ.get("FACTORY_CURSOR_BIN", "").strip()
    if override:
        reason = details[-1] if details else "not found"
        raise CursorCLIError(f"FACTORY_CURSOR_BIN is not a usable Cursor CLI: {reason}")
    if candidates:
        raise CursorCLIError(details[-1])
    raise CursorCLIError(
        "Cursor CLI not found. Install it from https://cursor.com/docs/cli/installation, "
        "then run `agent login`."
    )


def cursor_command(
    binary: str,
    *,
    read_only: bool,
    output_format: str = "json",
    environment: Mapping[str, str] | None = None,
) -> list[str]:
    """Build the one documented non-interactive command used by the Factory."""
    source = os.environ if environment is None else environment
    command = [
        binary,
        "--print",
        "--force",
        "--sandbox",
        "enabled",
        "--output-format",
        output_format,
    ]
    if read_only:
        command.extend(["--mode", "ask"])
    model = source.get("FACTORY_CURSOR_MODEL", "").strip()
    if model:
        command.extend(["--model", model])
    return command


def cursor_result(output: str) -> str:
    """Extract the assistant's final text from Cursor's JSON result envelope."""
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise CursorCLIError(f"Cursor returned invalid JSON output: {exc}") from exc
    if not isinstance(payload, dict):
        raise CursorCLIError("Cursor returned a non-object JSON result")
    if payload.get("type") != "result" or payload.get("subtype") != "success" or payload.get("is_error"):
        detail = redact_credentials(str(payload.get("result") or payload.get("error") or ""))[-2000:]
        raise CursorCLIError(f"Cursor did not return a successful result envelope: {detail}")
    result = payload.get("result")
    if not isinstance(result, str) or not result.strip():
        raise CursorCLIError("Cursor returned no final response text")
    return result


def invoke_cursor(
    binary: str,
    cwd: Path,
    prompt: str,
    *,
    read_only: bool,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run Cursor once and normalize its result to plain assistant text."""
    command = cursor_command(binary, read_only=read_only)
    issue = cursor_configuration_issue(cwd)
    if issue:
        return subprocess.CompletedProcess(command, 2, "", issue)
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=cursor_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(command, 127, "", str(exc))
    if completed.returncode:
        return completed
    try:
        result = cursor_result(completed.stdout)
    except CursorCLIError as exc:
        return subprocess.CompletedProcess(command, 1, "", str(exc))
    return subprocess.CompletedProcess(command, 0, result, completed.stderr)


def _tool_label(event: dict) -> str:
    call = event.get("tool_call", {})
    if not isinstance(call, dict) or not call:
        return "a repository tool"
    name = next(iter(call))
    if name.endswith("ToolCall"):
        name = name[:-8]
    words = []
    for character in name:
        if character.isupper() and words:
            words.append(" ")
        words.append(character.lower())
    return "".join(words) or "a repository tool"


def stream_cursor(binary: str, cwd: Path, prompt: str, *, read_only: bool) -> int:
    """Stream bounded Cursor tool activity, then emit the final response text."""
    issue = cursor_configuration_issue(cwd)
    if issue:
        print(issue, file=sys.stderr)
        return 2
    command = cursor_command(
        binary,
        read_only=read_only,
        output_format="stream-json",
    )
    prompt_stream = tempfile.TemporaryFile(mode="w+")
    prompt_stream.write(prompt)
    prompt_stream.seek(0)
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            text=True,
            stdin=prompt_stream,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=cursor_environment(),
        )
    except OSError as exc:
        prompt_stream.close()
        print(str(exc), file=sys.stderr)
        return 127
    assert process.stdout is not None
    final_result = ""
    saw_terminal_result = False
    for raw in process.stdout:
        line = raw.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            print(line, file=sys.stderr, flush=True)
            continue
        if not isinstance(event, dict):
            continue
        event_type = event.get("type")
        subtype = event.get("subtype")
        if event_type == "system" and subtype == "init":
            model = event.get("model")
            suffix = f" with {model}" if isinstance(model, str) and model else ""
            print(f"Cursor session initialized{suffix}.", flush=True)
        elif event_type == "tool_call" and subtype == "started":
            print(f"Cursor is using {_tool_label(event)}.", flush=True)
        elif event_type == "result":
            saw_terminal_result = True
            if subtype == "success" and not event.get("is_error"):
                result = event.get("result")
                if isinstance(result, str):
                    final_result = result
            else:
                message = event.get("result") or "Cursor returned an unsuccessful result."
                print(str(message), file=sys.stderr, flush=True)
    process.stdout.close()
    returncode = process.wait()
    prompt_stream.close()
    if returncode == 0 and (not saw_terminal_result or not final_result.strip()):
        print("Cursor returned no successful terminal result.", file=sys.stderr)
        return 1
    if final_result:
        print(final_result, flush=True)
    return returncode


def run_prompt(prompt_path: Path, *, read_only: bool) -> int:
    """Command-adapter entry point used by worker, QA, review, and supervisor roles."""
    if not prompt_path.is_file():
        print(f"Cursor prompt file not found: {prompt_path}", file=sys.stderr)
        return 2
    try:
        binary = resolve_cursor_cli(Path.cwd())
    except CursorCLIError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return stream_cursor(
        binary,
        Path.cwd(),
        prompt_path.read_text(),
        read_only=read_only,
    )


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Software (re)-Factory Cursor CLI adapter")
    subcommands = command.add_subparsers(dest="command", required=True)
    run = subcommands.add_parser("run", help="run a Factory prompt with Cursor")
    run.add_argument("--prompt", required=True, type=Path)
    run.add_argument("--read-only", action="store_true")
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "run":
        return run_prompt(args.prompt, read_only=args.read_only)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
