#!/usr/bin/env python3
"""Dependency-free cyclomatic-complexity report and regression gate.

The score is a conservative McCabe-style proxy: a function starts at one and
adds one for each branch, loop, exception handler, comprehension, match arm,
and short-circuit boolean decision. Nested functions are scored independently.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FunctionComplexity:
    path: Path
    name: str
    line: int
    lines: int
    score: int


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.score = 1

    def _decision(self, node: ast.AST) -> None:
        self.score += 1
        self.generic_visit(node)

    visit_If = _decision
    visit_IfExp = _decision
    visit_For = _decision
    visit_AsyncFor = _decision
    visit_While = _decision

    def visit_Try(self, node: ast.Try) -> None:
        self.score += len(node.handlers)
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.score += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self.score += 1 + len(node.ifs)
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        self.score += max(0, len(node.cases) - 1)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return


def function_complexities(root: Path) -> list[FunctionComplexity]:
    results: list[FunctionComplexity] = []
    for path in sorted(root.rglob("*.py")):
        if "tests" in path.parts or "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            visitor = ComplexityVisitor()
            for statement in node.body:
                visitor.visit(statement)
            results.append(FunctionComplexity(
                path=path,
                name=node.name,
                line=node.lineno,
                lines=(node.end_lineno or node.lineno) - node.lineno + 1,
                score=visitor.score,
            ))
    return sorted(results, key=lambda item: (-item.score, str(item.path), item.line))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path(__file__).parent)
    parser.add_argument("--limit", type=int, default=75)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()
    results = function_complexities(args.root.resolve())
    for item in results[:args.top]:
        print(
            f"{item.score:3}  {item.lines:4}  "
            f"{item.path}:{item.line}  {item.name}"
        )
    offenders = [item for item in results if item.score > args.limit]
    if offenders:
        print(f"\nFAIL: {len(offenders)} function(s) exceed complexity {args.limit}.")
        return 1
    print(f"\nPASS: no production function exceeds complexity {args.limit}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
