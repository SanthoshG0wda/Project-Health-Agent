import datetime
from pathlib import Path
from langchain.tools import tool
from .tool import extract_project_data
from .rag_engine import evaluate


@tool
def analyze_project(filepath: str, as_of_date: str | None = None):
    """Read an Excel project plan, extract structured data, determine RAG status, and return a complete health assessment.

    Args:
        filepath: Path to the Excel file containing the project plan.
        as_of_date: Date to evaluate against (YYYY-MM-DD). Defaults to today.
    """
    if not Path(filepath).exists():
        return f"File not found: {filepath}"

    as_of = datetime.datetime.strptime(as_of_date, "%Y-%m-%d") if as_of_date else datetime.datetime.now()

    data = extract_project_data.invoke({"filepath": filepath, "as_of_date": as_of})
    rag = evaluate.invoke({"data": data})

    ex = data
    signals = rag["signals"]
    lines = []

    lines.append(f"# Project Health Assessment: {ex['project_name']}")
    lines.append(f"**As of**: {ex['as_of_date'][:10]}")
    lines.append(f"**PM**: {ex.get('project_manager') or 'N/A'}")
    lines.append(f"**% Complete**: {ex.get('pct_complete') or 'N/A'}")
    lines.append(f"")
    lines.append(f"## Overall RAG: {rag['overall_status']}")
    lines.append(f"")

    for signal_name, info in signals.items():
        label = signal_name.replace("_", " ").title()
        lines.append(f"### {label}: {info['status']}")
        lines.append(f"{info['detail']}")
        lines.append(f"")

    if ex.get("budget", {}).get("total"):
        b = ex["budget"]
        lines.append(f"**Budget**: ${b['total']:,.0f} total, ${b['spent']:,.0f} spent")

    if ex.get("stakeholder_sentiment"):
        lines.append(f"**Stakeholder Sentiment**: {ex['stakeholder_sentiment']}")

    if ex.get("extraction_warnings"):
        lines.append(f"")
        lines.append(f"### Data Quality Notes")
        for w in ex["extraction_warnings"]:
            lines.append(f"- {w}")

    if rag["overall_status"] == "Red":
        lines.append(f"")
        lines.append(f"**Recommendation**: Escalate to leadership immediately.")
    elif rag["overall_status"] == "Amber":
        lines.append(f"")
        lines.append(f"**Recommendation**: Monitor closely and prepare mitigation plan.")
    else:
        lines.append(f"")
        lines.append(f"**Recommendation**: Project is on track.")

    return "\n".join(lines)
