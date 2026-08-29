#!/usr/bin/env python3
"""Minimal Factory Adapter Protocol v1 example.

This fixture intentionally performs no coding. Copy its event and result
framing into a real inner-harness adapter, then run ``factory adapter-check``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def emit(prefix: str, value: dict) -> None:
    print(prefix + json.dumps(value, separators=(",", ":")), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assignment", required=True)
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()
    assignment = json.loads(Path(args.assignment).read_text())
    prompt = Path(args.prompt)
    if assignment.get("schema_version") != 1 or not prompt.is_file():
        emit("FACTORY_RESULT ", {
            "schema_version": 1,
            "outcome": "blocked",
            "output_revisions": {},
            "artifacts": [],
            "verification_claims": [],
            "unresolved_risks": ["Assignment or prompt reference is invalid."],
        })
        return 2
    emit("FACTORY_EVENT ", {
        "schema_version": 1,
        "type": "status",
        "message": "Validated assignment and prompt references",
    })
    emit("FACTORY_RESULT ", {
        "schema_version": 1,
        "outcome": "success",
        "output_revisions": {},
        "artifacts": [],
        "verification_claims": ["Protocol framing completed."],
        "unresolved_risks": ["Example adapter does not modify product code."],
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
