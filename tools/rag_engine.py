"""
Deterministic RAG rule engine. Takes extracted project data + threshold
config, returns per-signal scores and an overall status. No LLM calls
here -- this must be auditable and reproducible on its own.
"""

import yaml
from langchain.tools import tool

def _load_thresholds(config_path):
    with open(config_path) as f:
        return yaml.safe_load(f)


def _score_schedule(data, cfg):
    tsh = data["task_schedule_health"]
    labeled_total = tsh["Red"] + tsh["Amber"] + tsh["Green"]
    if labeled_total == 0:
        return "insufficient_data", "No tasks had a labeled Schedule Health value."
    red_pct = tsh["Red"] / labeled_total
    t = cfg["schedule_slippage"]
    if red_pct <= t["green_max_pct"]:
        status = "Green"
    elif red_pct <= t["amber_max_pct"]:
        status = "Amber"
    else:
        status = "Red"
    detail = f"{tsh['Red']}/{labeled_total} tasks ({red_pct:.0%}) flagged Red for schedule health."
    return status, detail


def _score_budget(data, cfg):
    budget = data.get("budget", {})
    if not budget.get("total") or budget.get("spent") is None:
        return "insufficient_data", "No budget total/spend figures were present in the source file."
    burn_ratio = (budget["spent"] / budget["total"]) / max(data.get("pct_complete") or 0.0001, 0.0001)
    t = cfg["budget_burn"]
    if burn_ratio <= t["green_max_ratio"]:
        status = "Green"
    elif burn_ratio <= t["amber_max_ratio"]:
        status = "Amber"
    else:
        status = "Red"
    detail = f"Burn ratio (spend% / complete%) = {burn_ratio:.2f}"
    return status, detail


def _score_milestones(data, cfg):
    overdue = data["overdue_incomplete_tasks"]
    t = cfg["milestones"]
    if overdue <= t["green_max_overdue"]:
        status = "Green"
    elif overdue <= t["amber_max_overdue"]:
        status = "Amber"
    else:
        status = "Red"
    detail = f"{overdue} tasks are overdue (past End Date) and not marked Completed."
    return status, detail


def _score_blockers(data, cfg):
    overdue_critical = data["overdue_critical_tasks"]
    t = cfg["blockers"]
    if overdue_critical <= t["green_max"]:
        status = "Green"
    elif overdue_critical <= t["amber_max"]:
        status = "Amber"
    else:
        status = "Red"
    detail = (
        f"{overdue_critical} overdue tasks are flagged Critical (used as a blocker proxy; "
        f"no explicit 'blocker' field was present in the source file)."
    )
    return status, detail


def _score_sentiment(data, cfg):
    if not cfg["stakeholder_sentiment"]["enabled"] or data.get("stakeholder_sentiment") is None:
        return "insufficient_data", "No PM status-comment or sentiment source field was present in the source file."
    return data["stakeholder_sentiment"], "Derived from PM status comments."


_RANK = {"Green": 0, "Amber": 1, "Red": 2}

@tool
def evaluate(data: dict, config_path: str = "config/rag_thresholds.yaml"):
    """Evaluate RAG status of a project based on extracted project data.

    Args:
        data: The structured project data dict from extract_project_data tool.
        config_path: Path to the RAG thresholds YAML config file.
    """
    cfg = _load_thresholds(config_path)

    signals = {
        "schedule_slippage": _score_schedule(data, cfg),
        "budget_burn": _score_budget(data, cfg),
        "milestone_health": _score_milestones(data, cfg),
        "blockers": _score_blockers(data, cfg),
        "stakeholder_sentiment": _score_sentiment(data, cfg),
    }

    scored = {k: v[0] for k, v in signals.items() if v[0] in _RANK}
    reds = [k for k, v in scored.items() if v == "Red"]
    ambers = [k for k, v in scored.items() if v == "Amber"]

    if not scored:
        overall = "insufficient_data"
    elif len(reds) >= 2:
        overall = "Red"
    elif len(reds) == 1:
        # single-red cap rule: if every other scored signal is Green, cap at Amber
        others_all_green = all(v == "Green" for k, v in scored.items() if k not in reds)
        if cfg["aggregation"]["single_red_cap_to_amber"] and others_all_green:
            overall = "Amber"
        else:
            overall = "Red"
    elif ambers:
        overall = "Amber"
    else:
        overall = "Green"

    return {
        "overall_status": overall,
        "signals": {
            k: {"status": v[0], "detail": v[1]} for k, v in signals.items()
        },
    }


