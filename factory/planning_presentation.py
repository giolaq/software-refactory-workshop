"""One presentation contract for every planning-state consumer."""

from __future__ import annotations

from session_config import PLANNING_AGENTS


RETRYABLE_PLANNING_STATUSES = {
    "product_approved",
    "system_architecture_approved",
    "program_design_approved",
    "blocked",
    "stale_alignment",
    "planning_system_architecture",
    "planning_program_design",
    "planning_vertical_slices",
}
REPLAN_REQUIRED_STATUSES = {
    "stale_factory_charter",
    "stale_factory_profile",
    "stale_project_contract",
    "stale_product_review",
}


def planning_blocking_stage(planning: dict) -> dict | None:
    return next(
        (
            stage
            for stage in planning.get("stages", [])
            if stage.get("status") == "blocked" and stage.get("questions")
        ),
        None,
    )


def planning_failed_stage(planning: dict) -> dict | None:
    """Return a failed expert stage, excluding deliberate human-question pauses."""
    return next(
        (
            stage
            for stage in planning.get("stages", [])
            if stage.get("status") == "blocked"
            and not stage.get("questions")
            and any(
                stage.get(key)
                for key in (
                    "failure_kind", "error", "validation_error", "rejected_artifact",
                )
            )
        ),
        None,
    )


def planning_recovery(stage: dict | None, current_adapter: str, adapters: list[str]) -> dict:
    """Describe the safe recovery for one failed planning stage."""
    if not stage:
        return {}
    error = str(stage.get("error") or "")
    normalized = error.lower()
    alternatives = [
        name for name in adapters
        if name in PLANNING_AGENTS and name != current_adapter
    ]
    attempts = max(1, int(stage.get("failure_count") or 0))
    same_failure_count = max(
        1,
        int(stage.get("same_failure_count") or 0),
        attempts if not stage.get("same_failure_count") else 0,
    )
    recommended_adapter = alternatives[0] if alternatives else ""
    if stage.get("failure_kind") == "validation":
        kind = "validation"
        summary = "The artifact must be corrected before planning can continue."
        retry_same = False
        recommended_action = "correct_and_retry"
    elif any(marker in normalized for marker in (
        "session limit", "rate limit", "usage limit", "quota exceeded",
        "too many requests", "capacity",
    )):
        kind = "provider_capacity"
        summary = (
            f"{current_adapter.title() or 'The planning provider'} is unavailable or out of capacity. "
            "Retrying the same adapter now will repeat this failure."
        )
        retry_same = False
        recommended_action = "switch_adapter" if recommended_adapter else "wait"
    elif any(marker in normalized for marker in (
        "not logged in", "login required", "authentication", "unauthorized",
        "invalid api key", "missing openai api key", "api key",
    )):
        kind = "authentication"
        summary = "Repair the adapter login, then run preflight before retrying."
        retry_same = False
        recommended_action = "preflight"
    elif any(marker in normalized for marker in (
        "command not found", "no such file", "executable not found",
    )):
        kind = "adapter_setup"
        summary = "Install or configure the planning adapter, then run preflight."
        retry_same = False
        recommended_action = "preflight"
    elif same_failure_count >= 2:
        kind = "repeated_agent_failure"
        summary = (
            f"{current_adapter.title() or 'The planning adapter'} failed "
            f"{same_failure_count} times with the same error. "
            "Same-adapter retry is disabled; switch adapter and continue from the saved artifacts."
        )
        retry_same = False
        recommended_action = "switch_adapter" if recommended_adapter else "inspect_log"
    else:
        kind = "agent_process"
        summary = "The adapter process failed unexpectedly. Inspect the log, then retry explicitly."
        retry_same = True
        recommended_action = "retry_same_adapter"
    return {
        "kind": kind,
        "summary": summary,
        "retry_same_adapter": retry_same,
        "alternative_adapters": alternatives,
        "current_adapter": current_adapter,
        "recommended_action": recommended_action,
        "recommended_adapter": recommended_adapter,
        "attempts": attempts,
        "same_failure_count": same_failure_count,
    }


def planning_can_continue(planning: dict) -> bool:
    return (
        bool(planning.get("approvals", {}).get("product"))
        and planning.get("status") in RETRYABLE_PLANNING_STATUSES
        and planning_blocking_stage(planning) is None
    )


def _planning_sequence(planning: dict) -> list[dict]:
    stages = planning.get("stages", [])
    if not stages:
        return []
    required = set(
        planning.get("governance", {}).get("planning_approvals")
        or ["product_review", "alignment"]
    )
    required.update(planning.get("planning_controls", {}).get("planning_approvals") or [])
    approvals = planning.get("approvals", {})
    approval_keys = {
        "product_review": "product",
        "system_architecture": "system_architecture",
        "program_design": "program_design",
    }
    gate_titles = {
        "product_review": "Approve product",
        "system_architecture": "Approve architecture",
        "program_design": "Approve program design",
    }
    sequence = []
    for stage in stages:
        sequence.append(dict(stage))
        stage_id = stage.get("id")
        if stage_id not in required or stage_id == "vertical_slices":
            continue
        approval_key = approval_keys.get(stage_id)
        waiting = planning.get("status") == f"awaiting_{stage_id}_approval" or (
            stage_id == "product_review" and stage.get("status") == "complete"
        )
        sequence.append({
            "id": f"{stage_id}_gate",
            "stage": stage_id,
            "title": gate_titles.get(stage_id, "Approve planning stage"),
            "status": "approved" if approvals.get(approval_key) else "waiting" if waiting else "pending",
            "gate": True,
        })
    if "alignment" in required:
        sequence.append({
            "id": "alignment_gate",
            "title": "Approve alignment",
            "status": (
                "approved" if approvals.get("alignment")
                else "waiting" if planning.get("status") == "awaiting_alignment_approval"
                else "pending"
            ),
            "gate": True,
        })
    return sequence


def _replan_reason(planning: dict) -> str:
    return {
        "stale_factory_charter": "The approved Factory Charter changed or this run predates Charter governance.",
        "stale_factory_profile": planning.get(
            "planning_control_error",
            "The proposed paths require a stronger Factory Profile.",
        ),
        "stale_project_contract": "The Project Contract or detected repository inventory changed.",
        "stale_product_review": "The PRD copy changed after Product Review.",
    }.get(planning.get("status"), "Planning inputs changed.")


def _normalized_state(
    planning: dict,
    blocked_stage: dict | None,
    failed_stage: dict | None,
    recovery: dict,
) -> dict:
    """Classify raw lifecycle fields once for every presentation consumer."""
    status = planning.get("status", "")
    approvals = planning.get("approvals", {})
    product = next(
        (stage for stage in planning.get("stages", []) if stage.get("id") == "product_review"),
        {},
    )
    state = {
        "kind": "technical_ready",
        "status": status,
        "stage": {},
        "recovery": recovery,
        "replan_reason": "",
    }
    if status in REPLAN_REQUIRED_STATUSES:
        state.update({
            "kind": "replan",
            "stage": failed_stage or product,
            "replan_reason": _replan_reason(planning),
        })
    elif blocked_stage:
        state.update({"kind": "questions", "stage": blocked_stage})
    elif failed_stage:
        state.update({
            "kind": (
                "correction"
                if failed_stage.get("failure_kind") == "validation"
                else "recovery"
            ),
            "stage": failed_stage,
        })
    elif (
        product.get("status") == "complete"
        or status == "awaiting_product_approval"
    ) and not approvals.get("product"):
        state.update({"kind": "product_approval", "stage": product})
    elif status == "awaiting_system_architecture_approval" and not approvals.get("system_architecture"):
        state.update({
            "kind": "system_architecture_approval",
            "stage": next(
                (item for item in planning.get("stages", []) if item.get("id") == "system_architecture"),
                {},
            ),
        })
    elif status == "awaiting_program_design_approval" and not approvals.get("program_design"):
        state.update({
            "kind": "program_design_approval",
            "stage": next(
                (item for item in planning.get("stages", []) if item.get("id") == "program_design"),
                {},
            ),
        })
    elif status == "awaiting_alignment_approval" and not approvals.get("alignment"):
        state.update({"kind": "alignment_approval"})
    elif status in {"alignment_approved", "published"}:
        state.update({"kind": "complete"})
    elif not approvals.get("product"):
        state.update({"kind": "product_running", "stage": product})
    return state


def _decision(state: dict) -> dict | None:
    kind = state["kind"]
    stage = state.get("stage") or {}
    if kind == "replan":
        return {
            "kind": "replan",
            "title": "Restart planning safely",
            "text": state["replan_reason"],
            "view": "planning",
            "planning": stage.get("id") or "product_review",
            "queue_status": "Planning governance review",
            "queue_kind": "",
        }
    if kind == "questions":
        title = stage.get("title", "Planning")
        return {
            "kind": "questions",
            "title": f"Answer {title}",
            "text": f"{len(stage.get('questions', []))} decision(s) are blocking technical planning.",
            "view": "planning",
            "planning": stage.get("id", ""),
            "queue_status": f"{title} questions",
            "queue_kind": "question",
        }
    if kind in {"correction", "recovery"}:
        title = stage.get("title", "Planning expert")
        validation = kind == "correction"
        return {
            "kind": kind,
            "title": f"Correct {title}" if validation else f"Recover {title}",
            "text": state["recovery"].get("summary") or str(stage.get("error") or "Inspect the failure."),
            "view": "planning",
            "planning": stage.get("id", ""),
            "queue_status": f"{title} recovery",
            "queue_kind": "",
        }
    if kind == "product_approval":
        return {
            "kind": "approval",
            "title": "Approve Product Review",
            "text": "Confirm the user outcome before technical planning.",
            "view": "planning",
            "planning": "product_review_gate",
            "queue_status": "Product Review",
            "queue_kind": "approval",
        }
    approval_stages = {
        "system_architecture_approval": ("system_architecture", "System Architecture"),
        "program_design_approval": ("program_design", "Program Design"),
    }
    if kind in approval_stages:
        stage_id, title = approval_stages[kind]
        return {
            "kind": "approval",
            "title": f"Approve {title}",
            "text": "Confirm the exact expert artifact before downstream planning continues.",
            "view": "planning",
            "planning": f"{stage_id}_gate",
            "queue_status": f"{title} Review",
            "queue_kind": "approval",
        }
    if kind == "alignment_approval":
        return {
            "kind": "approval",
            "title": "Approve alignment",
            "text": "Accept architecture, program design, and vertical slices.",
            "view": "planning",
            "planning": "alignment_gate",
            "queue_status": "Alignment Review",
            "queue_kind": "approval",
        }
    return None


def _journey(state: dict) -> dict:
    kind = state["kind"]
    stage = state.get("stage") or {}
    recovery = state.get("recovery") or {}
    if kind == "replan":
        return {
            "phase_index": 2,
            "state": "blocked",
            "headline": "Planning governance changed",
            "detail": (
                "This run was invalidated because its PRD, Project Contract, or Factory Charter "
                "no longer matches the current approved repository rules. A retry cannot repair it."
            ),
            "next": {
                "label": "Restart planning safely",
                "detail": "Keep the saved PRD and regenerate the planning artifacts under the current governance.",
                "view": "planning",
            },
        }
    if kind == "questions":
        title = stage.get("title", "Planning expert")
        return {
            "phase_index": 2,
            "state": "attention",
            "headline": f"{title} is waiting for you",
            "detail": "Answer every blocking question in Planning. The expert will revise its artifact before downstream work resumes.",
            "next": {
                "label": "Answer blocked questions",
                "detail": "Open the blocked expert, record your decisions, and continue.",
                "view": "planning",
            },
        }
    if kind in {"correction", "recovery"}:
        title = stage.get("title", "Planning expert")
        failure = str(stage.get("error") or "").strip()
        validation = kind == "correction"
        if recovery.get("kind") == "provider_capacity":
            next_label = "Switch planning adapter or wait"
            next_detail = recovery.get("summary", "The current provider cannot run yet.")
        elif validation:
            next_label = f"Retry {title} with correction"
            next_detail = "The revision will reuse approved upstream work and include the validator feedback."
        else:
            next_label = "Open expert recovery"
            next_detail = recovery.get("summary", "Inspect the failure before choosing a recovery.")
        return {
            "phase_index": 2,
            "state": "blocked",
            "headline": f"{title} failed validation" if validation else f"{title} failed",
            "detail": failure[:420] or "The rejected artifact and failure evidence are available in Planning.",
            "next": {"label": next_label, "detail": next_detail, "view": "planning"},
        }
    if kind == "product_approval":
        return {
            "phase_index": 2,
            "state": "attention",
            "headline": "Product Review needs your decision",
            "detail": "Check the problem, user journey, scope, and measurable evidence before approving it.",
            "next": {
                "label": "Review Product Review",
                "detail": "Approve it or request a focused revision.",
                "view": "planning",
            },
        }
    if kind == "product_running":
        return {
            "phase_index": 2,
            "state": "ready",
            "headline": "Product Review is the current planning phase",
            "detail": "The product expert is preparing the behavior and evidence contract.",
            "next": {
                "label": "Open Planning",
                "detail": "Watch the expert output and inspect its artifact.",
                "view": "planning",
            },
        }
    if kind == "alignment_approval":
        return {
            "phase_index": 3,
            "state": "attention",
            "headline": "The delivery plan needs your approval",
            "detail": "Architecture, program design, and vertical slices are complete. No ticket is created until you approve alignment.",
            "next": {
                "label": "Review alignment",
                "detail": "Trace requirements through the four expert artifacts.",
                "view": "planning",
            },
        }
    stage_approvals = {
        "system_architecture_approval": "System Architecture",
        "program_design_approval": "Program Design",
    }
    if kind in stage_approvals:
        title = stage_approvals[kind]
        return {
            "phase_index": 2,
            "state": "attention",
            "headline": f"{title} needs your approval",
            "detail": (
                "The Factory Charter requires a person to approve this exact expert artifact "
                "before downstream planning can continue."
            ),
            "next": {
                "label": f"Review {title}",
                "detail": "Inspect the artifact, then approve its exact hash or request a revision.",
                "view": "planning",
            },
        }
    if kind == "complete":
        return {
            "phase_index": 3,
            "state": "complete",
            "headline": "Planning is complete",
            "detail": "The approved artifacts and vertical slices are ready for ticket delivery.",
            "next": {
                "label": "Open approved tickets",
                "detail": "Inspect the PRD-derived work before starting delivery.",
                "view": "tickets",
            },
        }
    return {
        "phase_index": 2,
        "state": "ready",
        "headline": "Technical planning is ready to run",
        "detail": "Architecture, program design, and vertical-slice experts run in sequence.",
        "next": {
            "label": "Run remaining experts",
            "detail": "Open Planning and start the remaining expert stages.",
            "view": "planning",
        },
    }


def planning_presentation(
    planning: dict,
    *,
    current_adapter: str = "",
    adapters: list[str] | None = None,
) -> dict:
    """Return the single operator-facing planning contract used by all callers."""
    blocked_stage = planning_blocking_stage(planning)
    failed_stage = planning_failed_stage(planning)
    recovery = planning_recovery(failed_stage, current_adapter, adapters or [])
    state = _normalized_state(planning, blocked_stage, failed_stage, recovery)
    kind = state["kind"]
    requires_replan = kind == "replan"
    requires_correction = kind == "correction"
    can_continue = (
        planning_can_continue(planning)
        and kind == "technical_ready"
    )
    continue_labels = {
        "replan": "Restart planning with current governance",
        "questions": "Answer expert questions",
        "recovery": "Open recovery options",
        "technical_ready": "Run remaining experts",
        "system_architecture_approval": "Review System Architecture",
        "program_design_approval": "Review Program Design",
        "product_approval": "Review Product Review",
        "alignment_approval": "Review alignment",
        "complete": "Planning complete",
        "product_running": "Continue planning",
    }
    continue_label = (
        f"Enter a correction for {(state.get('stage') or {}).get('title', 'expert')}"
        if kind == "correction"
        else continue_labels[kind]
    )
    decision = _decision(state)
    sequence = _planning_sequence(planning)
    selected_stage = (
        (decision or {}).get("planning")
        or (blocked_stage or {}).get("id")
        or (failed_stage or {}).get("id")
        or (sequence[0].get("id") if sequence else "")
    )
    return {
        "can_continue": can_continue,
        "state": kind,
        "requires_decisions": kind == "questions",
        "requires_correction": requires_correction,
        "requires_replan": requires_replan,
        "replan_reason": state["replan_reason"],
        "blocked_stage": (blocked_stage or {}).get("id", ""),
        "failed_stage": (failed_stage or {}).get("id", ""),
        "recovery": recovery,
        "continue_label": continue_label,
        "selected_stage": selected_stage,
        "decision": decision,
        "sequence": sequence,
        "journey": _journey(state),
    }
