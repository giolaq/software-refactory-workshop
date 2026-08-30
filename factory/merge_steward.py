"""Non-authoritative merge queue mechanics for exact reviewed revisions."""

from __future__ import annotations


class MergeSteward:
    """Assess or propose synchronization; never execute a merge."""

    def assess(self, candidate: dict) -> dict:
        head = str(candidate.get("candidate_head") or "")
        reviewed_head = str(candidate.get("reviewed_head") or "")
        result = {
            "schema_version": 1,
            "candidate_head": head,
            "reviewed_head": reviewed_head,
            "merge_authority": "human",
            "may_merge": False,
            "authorization_revoked": False,
            "required_after_change": [],
            "allowed_actions": [],
            "reasons": [],
        }
        base_changed = (
            candidate.get("candidate_base")
            and candidate.get("default_branch_head")
            and candidate.get("candidate_base") != candidate.get("default_branch_head")
        )
        if base_changed:
            return {
                **result,
                "state": "steward-updating",
                "authorization_revoked": True,
                "allowed_actions": ["synchronize-base"],
                "required_after_change": ["required-gates", "code-review"],
                "reasons": ["The default branch changed after the candidate was created."],
            }

        reasons = []
        if not head or head != reviewed_head:
            reasons.append("The candidate head is not the exact reviewed head.")
        if candidate.get("review_decision") != "approved":
            reasons.append("Code review has not approved the candidate.")
        if candidate.get("unresolved_comments"):
            reasons.append("Review comments remain unresolved.")
        if candidate.get("protected_paths_changed"):
            reasons.append("Protected paths changed and require a person to inspect them.")
        if candidate.get("acceptance_evidence_sha256") != candidate.get("reviewed_acceptance_evidence_sha256"):
            reasons.append("Acceptance evidence changed after review.")
        if candidate.get("branch_protection") != "passed":
            reasons.append("Branch protection is not satisfied.")
        gates = candidate.get("required_gates") or []
        if not gates or any(
            gate.get("status") != "passed" or gate.get("revision") != head
            for gate in gates
        ):
            reasons.append("Every required gate must pass on the exact candidate head.")
        if reasons:
            return {
                **result,
                "state": "human-decision-required",
                "authorization_revoked": True,
                "allowed_actions": ["inspect-evidence", "request-changes"],
                "reasons": reasons,
            }
        return {
            **result,
            "state": "ready-for-human-merge",
            "allowed_actions": ["present-exact-revision"],
            "reasons": ["Required gates and code review approve the exact candidate revision."],
        }

