"""Causal red/green evidence for QA-owned Acceptance Tests.

The module deliberately owns only two judgments: how to run the exact accepted
test files, and whether a complete runner result is a behavior assertion or an
execution problem. The orchestrator owns lifecycle decisions and persistence.
"""

from __future__ import annotations

import re
import shlex
import subprocess
import sys
from pathlib import Path, PurePosixPath


_COLLECTION_MARKERS = (
    "error collecting",
    "collection error",
    "modulenotfounderror",
    "no module named",
    "importerror",
    "cannot find module",
    "syntaxerror",
    "no tests ran",
    "no test files found",
    "test suite failed to run",
)
_ASSERTION_MARKERS = (
    "assertionerror",
    "err_assertion",
)


def bounded_runner_output(output: str) -> str:
    """Keep initial diagnostics and final summary; never use this for classification."""
    if len(output) <= 3000:
        return output
    return output[:1450] + "\n[intermediate output omitted]\n" + output[-1500:]


def focused_test_command(paths: list[str], python: str) -> str:
    """Return a shell-safe command that runs only the accepted QA files."""
    if not paths:
        raise ValueError("focused Acceptance Test command requires at least one test file")
    suffixes = {PurePosixPath(path).suffix.lower() for path in paths}
    quoted = " ".join(shlex.quote(path) for path in sorted(paths))
    if suffixes == {".py"}:
        return f"{shlex.quote(python)} -m pytest -q {quoted}"
    if suffixes <= {".js", ".cjs", ".mjs"}:
        return f"node --test {quoted}"
    if suffixes <= {".py", ".js", ".cjs", ".mjs"}:
        return f"{shlex.quote(python)} {shlex.quote(str(Path(__file__).resolve()))} {quoted}"
    raise ValueError(
        "no supported focused test runner for "
        + ", ".join(sorted(suffixes))
        + "; use Python pytest or Node.js test files"
    )


def classify_focused_result(exit_code: int, output: str) -> str:
    """Classify runner output without mistaking broken infrastructure for red."""
    lowered = output.lower()
    skipped = bool(
        re.search(r"\b[1-9]\d*[ \t]+skipped\b", lowered)
        or re.search(r"(?:#|ℹ)[ \t]*skipped[ \t]+[1-9]\d*\b", lowered)
    )
    if skipped:
        return "skipped"
    if exit_code == 0:
        return "pass"
    if exit_code == 124 or "timed out" in lowered:
        return "timeout"
    if exit_code == 127 or "command not found" in lowered:
        return "command_error"
    if any(marker in lowered for marker in _COLLECTION_MARKERS):
        return "collection_error"
    # A runner's FAILED/not-ok summary says nothing about the failure cause.
    # Mixed assertion + execution failures must not establish RED either.
    exceptions = re.findall(r"\b([a-z][a-z0-9_]*(?:error|exception))\b\s*:", lowered)
    if any(name != "assertionerror" for name in exceptions) or re.search(
        r"\b(?:enoent|eacces|econnrefused|enotfound)\b", lowered,
    ):
        return "unrelated_failure"
    if exit_code == 1 and any(marker in lowered for marker in _ASSERTION_MARKERS):
        return "behavior_assertion"
    return "unrelated_failure"


def run_focused_sets(paths: list[str], python: str) -> int:
    """Run every language group; an assertion cannot mask another runner's error."""
    focused_test_command(paths, python)  # Validate every suffix before executing.
    groups = (
        ("Python", [python, "-m", "pytest", "-q"], {".py"}),
        ("Node", ["node", "--test"], {".js", ".cjs", ".mjs"}),
    )
    classifications = []
    for name, command, suffixes in groups:
        selected = sorted(path for path in paths if PurePosixPath(path).suffix.lower() in suffixes)
        if not selected:
            continue
        print(f"Focused runner: {name}", flush=True)
        try:
            result = subprocess.run([*command, *selected], text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output = result.stdout
            classification = classify_focused_result(result.returncode, output)
        except OSError as exc:
            output = f"{name} command error: {exc}"
            classification = "command_error"
        print(output, end="\n", flush=True)
        print(f"Focused runner result: {name}: {classification}", flush=True)
        classifications.append(classification)
    if any(value not in {"pass", "behavior_assertion"} for value in classifications):
        return 2
    return 1 if "behavior_assertion" in classifications else 0


if __name__ == "__main__":
    raise SystemExit(run_focused_sets(sys.argv[1:], sys.executable))
