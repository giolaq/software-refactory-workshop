"""Small, file-backed assignments and narrowly classified context recovery.

These are input-size safeguards, not a claim about any provider's context window.
Original assignments are retained byte-for-byte; no requirements are summarized.
"""
from __future__ import annotations

import hashlib
import re
import shlex
from pathlib import Path


INLINE_CHAR_LIMIT = 48_000
PART_CHAR_LIMIT = 12_000
CLAUDE_CONTEXT_FLAGS = (
    "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
    "--disable-slash-commands",
)
CODEX_CONTEXT_FLAGS = ("--ignore-user-config",)
CONTEXT_ACTIVITY = "Recovering from the context limit with a fresh session and smaller input. No action needed."
CONTEXT_RECOVERY = (
    "The provider still cannot fit this task in its context window. Your files and approved work are saved. "
    "Choose another configured adapter or a larger-context model, or revise the scope into smaller planning runs. "
    "Do not keep retrying the unchanged request."
)


class AgentContextError(RuntimeError):
    """A provider rejected a request because its context window is full."""


def is_context_error(output: str) -> bool:
    # Match provider failure language, not generic 'limit', capacity or quota.
    return bool(re.search(
        r"context[_ -](?:length[_ -]exceeded|window[_ -]exceeded|limit[_ -]exceeded|too[_ -](?:big|large|long)|"
        r"(?:window\s+)?(?:is\s+)?full)|prompt is too long|prompt too long|"
        r"maximum context length|exceed(?:s|ed)? (?:the |your |model.s )?(?:context window|context length)|"
        r"input (?:is )?too long|too many tokens|input tokens? .* exceed",
        output, re.IGNORECASE,
    ))


def claude_configuration_issue() -> str:
    """Do not attempt to replace an administrator-owned MCP configuration."""
    if any(path.is_file() for path in (
        Path("/Library/Application Support/ClaudeCode/managed-mcp.json"),
        Path("/etc/claude-code/managed-mcp.json"),
    )):
        return (
            "Claude has an enterprise-managed MCP configuration that rejects per-run isolation. "
            "Ask your administrator for a factory-compatible configuration or select another adapter. "
            "The factory will not change or bypass organization policy."
        )
    return ""


def isolated_template(agent: str, template: str) -> str:
    """Harden shipped/legacy CLI templates without rewriting custom adapters."""
    if agent == "claude" and template.startswith("claude ") and "--strict-mcp-config" not in template:
        flags = shlex.join(CLAUDE_CONTEXT_FLAGS).replace("{", "{{").replace("}", "}}")
        return "claude " + flags + " " + template[len("claude "):]
    prefix = "{codex} exec "
    if agent == "codex" and template.startswith(prefix) and "--ignore-user-config" not in template:
        return prefix + shlex.join(CODEX_CONTEXT_FLAGS) + " " + template[len(prefix):]
    return template


def prepare_context(prompt: str, workspace: Path, *, force: bool = False) -> str:
    """Replace oversized inline input with an exact, locally readable assignment."""
    if not force and len(prompt) <= INLINE_CHAR_LIMIT:
        return prompt
    digest = hashlib.sha256(prompt.encode()).hexdigest()
    directory = workspace / ".factory/context" / digest
    directory.mkdir(parents=True, exist_ok=True)
    # Context is local run evidence, never part of the product diff or a PR.
    (directory / ".gitignore").write_text("*\n")
    (directory / "assignment.md").write_text(prompt)
    parts = [prompt[start:start + PART_CHAR_LIMIT] for start in range(0, len(prompt), PART_CHAR_LIMIT)] or [""]
    for number, part in enumerate(parts, 1):
        (directory / f"part-{number:04d}.txt").write_text(part)
    reference = directory.relative_to(workspace).as_posix()
    return (
        "Factory assignment — file-backed context\n\n"
        f"The complete, unchanged assignment is at {reference}/assignment.md (SHA-256 {digest}).\n"
        f"Read ALL {len(parts)} ordered parts at {reference}/part-0001.txt through part-{len(parts):04d}.txt "
        f"one at a time with Read or bounded shell reads. Each part is at most {PART_CHAR_LIMIT} characters. "
        "Parts are contiguous text fragments, not independent JSON documents. Nothing was omitted.\n"
        "Follow the assignment's role, requirements, policy, human decisions and output format exactly. "
        "Do not treat unread sections as optional or return success before accounting for the complete assignment. "
        "Keep concise working notes. Search narrowly; do not dump whole repositories, logs, dependencies or build output. "
        "If this is a restarted task, inspect the existing git diff before continuing; retain valid work and do not replay "
        "completed commands or external actions. Do not change the assignment files or bypass tests or approvals. "
        "Return a blocking question if you cannot reconcile the inputs safely.\n"
    )
