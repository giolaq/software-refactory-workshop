"""Reviewed cross-run improvement proposals from bounded factory evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


SEVERITIES = {"low", "medium", "high", "critical"}
UNAVAILABLE_USAGE = {
    "model": "unavailable", "input_tokens": "unavailable",
    "output_tokens": "unavailable", "duration_seconds": "unavailable",
    "cost": "unavailable",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class CompoundingEngine:
    """Aggregate evidence without changing delivery configuration or authority."""

    def __init__(self, repo: Path):
        self.repo = repo.resolve()
        self.runtime = self.repo / ".factory/improvements"
        self.signal_path = self.runtime / "observations.jsonl"
        self.usage_path = self.runtime / "usage.jsonl"
        self.report_path = self.runtime / "report.json"
        self.decision_path = self.runtime / "decisions.jsonl"

    @staticmethod
    def _append(path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as stream:
            stream.write(json.dumps(value, sort_keys=True) + "\n")

    @staticmethod
    def _read(path: Path) -> list[dict]:
        try:
            lines = path.read_text().splitlines()
        except OSError:
            return []
        result = []
        for line in lines:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                result.append(value)
        return result

    def record(self, category: str, signal: str, severity: str, evidence_ref: str, detail: str) -> dict:
        if severity not in SEVERITIES:
            raise ValueError("severity must be low, medium, high, or critical")
        category = str(category).strip()[:80]
        signal = str(signal).strip()[:120]
        evidence_ref = str(evidence_ref).strip()[:300]
        if not category or not signal or not evidence_ref:
            raise ValueError("category, signal, and evidence_ref are required")
        observation_id = hashlib.sha256(
            f"{category}:{signal}:{evidence_ref}".encode()
        ).hexdigest()[:20]
        existing = next(
            (
                item for item in self._read(self.signal_path)
                if item.get("observation_id") == observation_id
                or (
                    item.get("category") == category
                    and item.get("signal") == signal
                    and item.get("evidence_ref") == evidence_ref
                )
            ),
            None,
        )
        if existing:
            return existing
        value = {
            "observation_id": observation_id,
            "observed_at": _now(), "category": category,
            "signal": signal, "severity": severity,
            "evidence_ref": evidence_ref, "detail": str(detail)[:1000],
        }
        self._append(self.signal_path, value)
        return value

    @staticmethod
    def _slug(value: str, fallback: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "-", str(value).casefold()).strip("-")
        return (normalized or fallback)[:120]

    def collect_repository_evidence(self) -> int:
        """Collect already-retained bounded run evidence without duplicating it."""
        before = len(self._read(self.signal_path))
        try:
            state = json.loads((self.repo / ".factory/state.json").read_text())
        except (OSError, json.JSONDecodeError):
            state = {}
        run_id = str(state.get("run_id") or "local-run")[:80]
        for ticket in state.get("tickets", []) if isinstance(state, dict) else []:
            if not isinstance(ticket, dict):
                continue
            number = ticket.get("number", "unknown")
            evidence_ref = f"run/{run_id}#ticket-{number}"
            metrics = ticket.get("metrics") if isinstance(ticket.get("metrics"), dict) else {}
            retry_count = metrics.get("retry_count", 0)
            if isinstance(retry_count, int) and retry_count > 0:
                self.record(
                    "qa", "ticket-retry", "medium", evidence_ref,
                    f"Ticket recorded {retry_count} retry attempt(s).",
                )
            verifier_rejections = metrics.get("verifier_rejections", 0)
            if isinstance(verifier_rejections, int) and verifier_rejections > 0:
                self.record(
                    "qa", "verifier-rejection", "medium", evidence_ref,
                    f"Ticket recorded {verifier_rejections} verifier rejection(s).",
                )
            failure = str(ticket.get("failure") or "")
            if "already pass" in failure.casefold() or "already green" in failure.casefold():
                self.record(
                    "qa", "acceptance-test-already-green", "high", evidence_ref,
                    failure,
                )
            budget = ticket.get("diff_budget") if isinstance(ticket.get("diff_budget"), dict) else {}
            if budget.get("status") in {"exceeded", "exception-approved"}:
                self.record(
                    "review", "diff-budget-exception", "high", evidence_ref,
                    json.dumps(budget, sort_keys=True)[:1000],
                )
            review = ticket.get("code_review") if isinstance(ticket.get("code_review"), dict) else {}
            result = review.get("result") if isinstance(review.get("result"), dict) else {}
            findings = result.get("findings")
            if not isinstance(findings, list):
                findings = []
            for index, finding in enumerate(findings[:20]):
                if not isinstance(finding, dict):
                    continue
                signal = self._slug(
                    finding.get("kind") or finding.get("category") or finding.get("title"),
                    "code-review-finding",
                )
                self.record(
                    "review", signal, "medium",
                    f"{evidence_ref}/review-{index + 1}",
                    finding.get("message") or finding.get("detail") or signal,
                )

        monitor_path = self.repo / ".factory/monitor/report.json"
        try:
            monitor = json.loads(monitor_path.read_text())
        except (OSError, json.JSONDecodeError):
            monitor = {}
        monitor_findings = monitor.get("findings") if isinstance(monitor, dict) else []
        if not isinstance(monitor_findings, list):
            monitor_findings = []
        for index, finding in enumerate(monitor_findings[:100]):
            if not isinstance(finding, dict):
                continue
            severity = str(finding.get("severity") or "low").casefold()
            normalized_severity = (
                "high" if severity in {"blocking", "critical", "high"}
                else "medium" if severity in {"warning", "medium"}
                else "low"
            )
            signal = self._slug(finding.get("kind"), "monitor-finding")
            evidence_ref = str(finding.get("path") or f"monitor/finding-{index + 1}")
            self.record(
                "monitor", signal, normalized_severity, evidence_ref,
                finding.get("message") or finding.get("detail") or signal,
            )

        revisions_root = self.repo / ".factory/plans"
        for path in sorted(revisions_root.glob("*/revisions/*.json"))[:500]:
            try:
                value = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            stage = self._slug(
                value.get("stage") if isinstance(value, dict) else path.stem,
                "planning-correction",
            )
            self.record(
                "planning", f"{stage}-correction", "medium",
                str(path.relative_to(self.repo)),
                (value.get("feedback") if isinstance(value, dict) else "")
                or "A person requested a planning artifact correction.",
            )
        return len(self._read(self.signal_path)) - before

    def record_usage(self, adapter: str, usage: dict) -> dict:
        trustworthy = usage.get("trustworthy") is True
        value = {
            "observed_at": _now(), "adapter": str(adapter)[:80],
            **(
                {
                    "model": usage.get("model", "unavailable"),
                    "input_tokens": usage.get("input_tokens", "unavailable"),
                    "output_tokens": usage.get("output_tokens", "unavailable"),
                    "duration_seconds": usage.get("duration_seconds", "unavailable"),
                    "cost": usage.get("cost", "unavailable"),
                    "trustworthy": True,
                }
                if trustworthy else {**UNAVAILABLE_USAGE, "trustworthy": False}
            ),
        }
        self._append(self.usage_path, value)
        return value

    def build_report(self) -> dict:
        self.collect_repository_evidence()
        groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for item in self._read(self.signal_path):
            groups[(item.get("category", ""), item.get("signal", ""))].append(item)
        suggestions = []
        for (category, signal), observations in sorted(groups.items()):
            severe = any(item.get("severity") in {"high", "critical"} for item in observations)
            if len(observations) < 2 and not severe:
                continue
            evidence = [item.get("evidence_ref", "") for item in observations if item.get("evidence_ref")]
            suggestion_id = hashlib.sha256(f"{category}:{signal}".encode()).hexdigest()[:12]
            suggestions.append({
                "id": suggestion_id,
                "status": "proposed",
                "human_decision": "pending",
                "category": category,
                "signal": signal,
                "observation_count": len(observations),
                "evidence": evidence,
                "proposal": self._proposal(category, signal),
                "expected_effect": f"Reduce recurrence of {signal.replace('-', ' ')}.",
                "possible_regression": "A narrower rule may reject a valid variation or add review work.",
                "verification_plan": "Replay the same retained cases before and after the human-reviewed change.",
            })
        latest_usage = {}
        for item in self._read(self.usage_path):
            latest_usage[item.get("adapter", "unknown")] = {
                key: item.get(key, "unavailable")
                for key in UNAVAILABLE_USAGE
            }
        report = {
            "schema_version": 1,
            "generated_at": _now(),
            "authority": {
                "owner": "human",
                "may_edit_charter": False,
                "may_change_delivery_configuration": False,
                "accepted_changes_require_pull_request": True,
            },
            "observation_count": sum(len(values) for values in groups.values()),
            "suggestions": suggestions,
            "usage": latest_usage,
        }
        self.runtime.mkdir(parents=True, exist_ok=True)
        temporary = self.report_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, indent=2) + "\n")
        os.replace(temporary, self.report_path)
        self._write_markdown(report)
        return report

    @staticmethod
    def _proposal(category: str, signal: str) -> str:
        choices = {
            "planning": "Review the role prompt or schema fixture.",
            "qa": "Add or correct a deterministic causal verification gate.",
            "review": "Review the implementation prompt or add a focused deterministic check.",
            "monitor": "Correct the Project Contract or recovery documentation.",
            "adapter": "Review capability fit for this role and consider another Adapter.",
        }
        return choices.get(category, f"Review the outer-harness contract associated with {signal}.")

    def _write_markdown(self, report: dict) -> None:
        lines = [
            "# Factory improvement report", "",
            "> Suggestions only. A human-reviewed pull request is required; this report cannot edit the Factory Charter.", "",
        ]
        if not report["suggestions"]:
            lines.append("No signal met the evidence threshold.")
        for suggestion in report["suggestions"]:
            lines.extend([
                f"## {suggestion['signal']}", "",
                suggestion["proposal"], "",
                f"- Evidence: {', '.join(suggestion['evidence'])}",
                f"- Expected effect: {suggestion['expected_effect']}",
                f"- Possible regression: {suggestion['possible_regression']}",
                f"- Verification: {suggestion['verification_plan']}", "",
            ])
        (self.runtime / "report.md").write_text("\n".join(lines).rstrip() + "\n")

    def decide(self, suggestion_id: str, decision: str, reason: str) -> dict:
        if decision not in {"accepted", "rejected"}:
            raise ValueError("decision must be accepted or rejected")
        report = self.build_report()
        if suggestion_id not in {item["id"] for item in report["suggestions"]}:
            raise ValueError("improvement suggestion not found")
        value = {
            "decided_at": _now(), "suggestion_id": suggestion_id,
            "decision": decision, "reason": str(reason)[:2000],
            "configuration_changed": False, "charter_changed": False,
        }
        self._append(self.decision_path, value)
        return value
