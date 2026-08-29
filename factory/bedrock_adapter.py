#!/usr/bin/env python3
"""Bounded Amazon Bedrock adapter for planning and repository editing.

This is the inner harness used by the AWS deployment.  Bedrock receives a
small, explicit tool surface instead of an arbitrary shell.  The outer Factory
remains responsible for running approved verification gates and publishing
GitHub changes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


MAX_PROMPT = 400_000
MAX_WRITE = 1_000_000
MAX_READ = 200_000
MAX_RESULTS = 200


class BedrockAdapterError(RuntimeError):
    """A bounded, user-facing adapter failure."""


def emit_event(event_type: str, message: str = "", **extra: Any) -> None:
    event = {"schema_version": 1, "type": event_type}
    if message:
        event["message"] = message[:1000]
    event.update(extra)
    print("FACTORY_EVENT " + json.dumps(event, separators=(",", ":")), flush=True)


class WorkspaceTools:
    """Constrain all model-visible file operations to one worktree."""

    def __init__(self, root: Path, *, read_only: bool = False):
        self.root = root.resolve()
        self.read_only = read_only
        if not self.root.is_dir():
            raise BedrockAdapterError(f"workspace does not exist: {self.root}")

    def _path(self, raw: str, *, allow_root: bool = False) -> Path:
        if not isinstance(raw, str) or "\x00" in raw:
            raise BedrockAdapterError("tool path must be a string")
        candidate = (self.root / raw).resolve()
        try:
            relative = candidate.relative_to(self.root)
        except ValueError as exc:
            raise BedrockAdapterError("tool path escapes the assigned workspace") from exc
        if not allow_root and relative == Path("."):
            raise BedrockAdapterError("tool path must identify a file")
        return candidate

    def list_files(self, path: str = ".") -> dict:
        base = self._path(path, allow_root=True)
        if not base.is_dir():
            raise BedrockAdapterError("list_files path must be a directory")
        files: list[str] = []
        for current, directories, names in os.walk(base, followlinks=False):
            directories[:] = sorted(
                name for name in directories if name not in {".git", ".factory"}
            )
            for name in sorted(names):
                candidate = Path(current) / name
                if candidate.is_file():
                    files.append(candidate.relative_to(self.root).as_posix())
                if len(files) >= MAX_RESULTS:
                    return {"files": files, "truncated": True}
        return {"files": files, "truncated": len(files) == MAX_RESULTS}

    def read_file(self, path: str, start_line: int = 1, end_line: int = 400) -> dict:
        target = self._path(path)
        if not target.is_file():
            raise BedrockAdapterError("read_file path must be an existing file")
        if not isinstance(start_line, int) or not isinstance(end_line, int):
            raise BedrockAdapterError("line bounds must be integers")
        if start_line < 1 or end_line < start_line or end_line - start_line > 2000:
            raise BedrockAdapterError("read_file line range is invalid or too large")
        lines = target.read_text(errors="replace").splitlines()
        content = "\n".join(lines[start_line - 1:end_line])[:MAX_READ]
        return {
            "path": target.relative_to(self.root).as_posix(),
            "start_line": start_line,
            "end_line": min(end_line, len(lines)),
            "total_lines": len(lines),
            "content": content,
        }

    def search_text(self, query: str, path: str = ".") -> dict:
        if not isinstance(query, str) or not query or len(query) > 500:
            raise BedrockAdapterError("search query must contain 1 to 500 characters")
        base = self._path(path, allow_root=True)
        if base.is_file():
            candidates = [base]
        else:
            candidates = []
            for current, directories, names in os.walk(base, followlinks=False):
                directories[:] = [
                    name for name in directories if name not in {".git", ".factory"}
                ]
                candidates.extend(Path(current) / name for name in names)
        matches: list[dict] = []
        needle = query.casefold()
        for candidate in candidates:
            if not candidate.is_file():
                continue
            relative = candidate.relative_to(self.root)
            if any(part in {".git", ".factory"} for part in relative.parts):
                continue
            try:
                if candidate.stat().st_size > MAX_READ:
                    continue
                for number, line in enumerate(candidate.read_text(errors="replace").splitlines(), 1):
                    if needle in line.casefold():
                        matches.append({
                            "path": relative.as_posix(), "line": number, "text": line[:500],
                        })
                        if len(matches) >= MAX_RESULTS:
                            return {"matches": matches, "truncated": True}
            except OSError:
                continue
        return {"matches": matches, "truncated": False}

    def write_file(self, path: str, content: str) -> dict:
        if self.read_only:
            raise BedrockAdapterError("this assignment is read-only")
        if not isinstance(content, str) or len(content.encode()) > MAX_WRITE:
            raise BedrockAdapterError("write_file content exceeds the 1 MB limit")
        target = self._path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return {"path": target.relative_to(self.root).as_posix(), "bytes": len(content.encode())}

    def delete_file(self, path: str) -> dict:
        if self.read_only:
            raise BedrockAdapterError("this assignment is read-only")
        target = self._path(path)
        if not target.is_file():
            raise BedrockAdapterError("delete_file path must be an existing file")
        relative = target.relative_to(self.root).as_posix()
        target.unlink()
        return {"path": relative, "deleted": True}

    def dispatch(self, name: str, value: dict) -> dict:
        if not isinstance(value, dict):
            raise BedrockAdapterError("tool input must be an object")
        methods = {
            "list_files": self.list_files,
            "read_file": self.read_file,
            "search_text": self.search_text,
            "write_file": self.write_file,
            "delete_file": self.delete_file,
        }
        if name not in methods:
            raise BedrockAdapterError(f"unsupported tool: {name}")
        return methods[name](**value)


def _object_schema(properties: dict, required: list[str] | None = None) -> dict:
    value = {"type": "object", "properties": properties, "additionalProperties": False}
    if required:
        value["required"] = required
    return value


def repository_tool_specs(read_only: bool) -> list[dict]:
    specs = [
        ("list_files", "List repository files below a directory.", _object_schema({"path": {"type": "string"}})),
        ("read_file", "Read a bounded line range from a repository file.", _object_schema({
            "path": {"type": "string"}, "start_line": {"type": "integer"},
            "end_line": {"type": "integer"},
        }, ["path"])),
        ("search_text", "Search for fixed text in repository files.", _object_schema({
            "query": {"type": "string"}, "path": {"type": "string"},
        }, ["query"])),
    ]
    if not read_only:
        specs.extend([
            ("write_file", "Create or replace one repository file.", _object_schema({
                "path": {"type": "string"}, "content": {"type": "string"},
            }, ["path", "content"])),
            ("delete_file", "Delete one repository file.", _object_schema({
                "path": {"type": "string"},
            }, ["path"])),
        ])
    return [{"toolSpec": {"name": name, "description": description, "inputSchema": {"json": schema}}}
            for name, description, schema in specs]


class BedrockAdapter:
    """Translate the Factory adapter interface to Bedrock Converse."""

    def __init__(self, client, model_id: str, *, max_turns: int = 24):
        if not model_id:
            raise BedrockAdapterError("FACTORY_BEDROCK_MODEL_ID is required")
        self.client = client
        self.model_id = model_id
        self.max_turns = max_turns

    def _converse(self, **kwargs):
        return self.client.converse(
            modelId=self.model_id,
            inferenceConfig={"maxTokens": 8192, "temperature": 0.1},
            **kwargs,
        )

    def run(self, prompt: str, workspace: Path, *, read_only: bool = False) -> str:
        tools = WorkspaceTools(workspace, read_only=read_only)
        messages = [{"role": "user", "content": [{"text": prompt[:MAX_PROMPT]}]}]
        system = [{"text": (
            "You are a coding agent inside a governed software factory. Use only the supplied "
            "repository tools. Work only on the requested assignment. Do not claim that tests passed: "
            "the outer factory runs approved verification gates after you finish. Return the exact "
            "structured response requested by the assignment when it asks for JSON."
        )}]
        usage = {"input_tokens": 0, "output_tokens": 0}
        for _ in range(self.max_turns):
            response = self._converse(
                system=system,
                messages=messages,
                toolConfig={"tools": repository_tool_specs(read_only), "toolChoice": {"auto": {}}},
            )
            metrics = response.get("usage", {})
            usage["input_tokens"] += int(metrics.get("inputTokens", 0))
            usage["output_tokens"] += int(metrics.get("outputTokens", 0))
            message = response.get("output", {}).get("message", {})
            content = message.get("content", [])
            tool_uses = [item["toolUse"] for item in content if "toolUse" in item]
            if not tool_uses:
                text = "\n".join(item["text"] for item in content if "text" in item).strip()
                if not text:
                    raise BedrockAdapterError("Bedrock returned no final response")
                emit_event("usage", usage=usage)
                return text
            messages.append(message)
            results = []
            for tool_use in tool_uses:
                name = tool_use.get("name", "")
                emit_event("tool_activity", f"Bedrock is using {name}.", tool=name or "unknown")
                try:
                    value = tools.dispatch(name, tool_use.get("input", {}))
                    status = "success"
                except (BedrockAdapterError, OSError, TypeError) as exc:
                    value = {"error": str(exc)[:1000]}
                    status = "error"
                results.append({"toolResult": {
                    "toolUseId": tool_use.get("toolUseId", "unknown"),
                    "content": [{"json": value}], "status": status,
                }})
            messages.append({"role": "user", "content": results})
        raise BedrockAdapterError(f"Bedrock exceeded the {self.max_turns}-turn tool limit")

    def structured_plan(self, prompt: str, schema: dict) -> dict:
        tool = {"toolSpec": {
            "name": "submit_artifact",
            "description": "Submit the complete planning artifact that satisfies the JSON Schema.",
            "inputSchema": {"json": schema},
        }}
        response = self._converse(
            system=[{"text": (
                "You are an expert in a human-gated software planning pipeline. Analyze the supplied "
                "PRD and repository context, then submit one complete artifact through submit_artifact."
            )}],
            messages=[{"role": "user", "content": [{"text": prompt[:MAX_PROMPT]}]}],
            toolConfig={"tools": [tool], "toolChoice": {"tool": {"name": "submit_artifact"}}},
        )
        content = response.get("output", {}).get("message", {}).get("content", [])
        for item in content:
            use = item.get("toolUse", {})
            if use.get("name") == "submit_artifact" and isinstance(use.get("input"), dict):
                return use["input"]
        raise BedrockAdapterError("Bedrock did not submit the required structured planning artifact")


def build_adapter() -> BedrockAdapter:
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    model_id = os.environ.get("FACTORY_BEDROCK_MODEL_ID", "").strip()
    if not region:
        raise BedrockAdapterError("AWS_REGION or AWS_DEFAULT_REGION is required")
    try:
        import boto3
    except ImportError as exc:
        raise BedrockAdapterError("boto3 is required for the Bedrock adapter") from exc
    try:
        turns = int(os.environ.get("FACTORY_BEDROCK_MAX_TURNS", "24"))
    except ValueError as exc:
        raise BedrockAdapterError("FACTORY_BEDROCK_MAX_TURNS must be an integer") from exc
    return BedrockAdapter(boto3.client("bedrock-runtime", region_name=region), model_id, max_turns=turns)


def main() -> int:
    parser = argparse.ArgumentParser(description="Amazon Bedrock Factory adapter")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--prompt", required=True)
    run.add_argument("--workspace", required=True)
    run.add_argument("--read-only", action="store_true")
    plan = sub.add_parser("plan")
    plan.add_argument("--schema", required=True)
    args = parser.parse_args()
    try:
        adapter = build_adapter()
        if args.command == "run":
            prompt = Path(args.prompt).read_text()
            if len(prompt) > MAX_PROMPT:
                raise BedrockAdapterError("prompt exceeds the adapter input limit")
            print(adapter.run(prompt, Path(args.workspace), read_only=args.read_only), flush=True)
        else:
            prompt = sys.stdin.read(MAX_PROMPT + 1)
            if len(prompt) > MAX_PROMPT:
                raise BedrockAdapterError("planning prompt exceeds the adapter input limit")
            schema = json.loads(Path(args.schema).read_text())
            print(json.dumps(adapter.structured_plan(prompt, schema)), flush=True)
        return 0
    except (BedrockAdapterError, OSError, json.JSONDecodeError) as exc:
        print(f"bedrock adapter: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
