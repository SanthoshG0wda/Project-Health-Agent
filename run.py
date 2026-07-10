import argparse
import datetime
import json
import os
import sys
import glob
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tools.tool import extract_project_data
from tools.rag_engine import evaluate


def process_file(filepath: str, as_of_date: datetime.datetime | None = None) -> dict:
    as_of_date = as_of_date or datetime.datetime.now()
    data = extract_project_data.invoke({"filepath": filepath, "as_of_date": as_of_date})
    result = evaluate.invoke({"data": data})
    return {"extracted": data, "rag": result}


def generate_report(project: dict) -> str:
    ex = project["extracted"]
    rag = project["rag"]
    lines = []
    lines.append(f"# Weekly Project Health Report")
    lines.append(f"**Project**: {ex['project_name']}")
    lines.append(f"**As of**: {ex['as_of_date'][:10]}")
    lines.append(f"**PM**: {ex['project_manager'] or 'N/A'}")
    lines.append(f"**Overall RAG**: {rag['overall_status']}")
    lines.append(f"**% Complete**: {ex['pct_complete'] or 'N/A'}")
    lines.append("")
    lines.append("## Signal Breakdown")
    for signal, info in rag["signals"].items():
        lines.append(f"- **{signal.replace('_', ' ').title()}**: {info['status']}")
        lines.append(f"  {info['detail']}")
    lines.append("")
    if ex["budget"]["total"]:
        lines.append(f"**Budget**: ${ex['budget']['total']:,.0f} total, ${ex['budget']['spent']:,.0f} spent")
    lines.append("")
    if ex["extraction_warnings"]:
        lines.append("## Data Quality Notes")
        for w in ex["extraction_warnings"]:
            lines.append(f"- {w}")
    lines.append("")
    if rag["overall_status"] == "Red":
        lines.append("**Action Required**: Escalate to leadership.")
    elif rag["overall_status"] == "Amber":
        lines.append("**Action Required**: Monitor closely, prepare mitigation plan.")
    else:
        lines.append("**Status**: On track.")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Project Health Reporting Agent")
    parser.add_argument("files", nargs="*", help="Specific Excel files to process")
    parser.add_argument("--output-dir", default="docs/reports", help="Output directory")
    parser.add_argument("--date", default=None, help="As-of date (YYYY-MM-DD)")
    parser.add_argument("--schedule", action="store_true", help="Run in schedule mode (for cron)")
    args = parser.parse_args()

    as_of = datetime.datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.datetime.now()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True)

    if args.files:
        files = args.files
    else:
        files = sorted(glob.glob("data/*.xlsx"))

    if not files:
        print("No Excel files found.")
        return

    week_label = as_of.strftime("%Y-%m-%d")
    week_dir = out_dir / week_label
    week_dir.mkdir(exist_ok=True)

    all_results = []

    for f in files:
        name = Path(f).stem.replace(" ", "_")
        print(f"Processing: {f}")
        try:
            project = process_file(f, as_of)
            all_results.append(project)

            report = generate_report(project)
            report_path = week_dir / f"{name}_report.md"
            report_path.write_text(report)
            print(f"  Report saved: {report_path}")

            json_path = week_dir / f"{name}_data.json"
            json_path.write_text(json.dumps(project, indent=2, default=str))
            print(f"  Data saved: {json_path}")

            print(f"  RAG: {project['rag']['overall_status']}")
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)

    summary = {"week": week_label, "as_of_date": as_of.isoformat(), "projects": []}
    for p in all_results:
        summary["projects"].append({
            "name": p["extracted"]["project_name"],
            "overall": p["rag"]["overall_status"],
            "pm": p["extracted"]["project_manager"],
            "pct_complete": p["extracted"]["pct_complete"],
            "signals": {k: v["status"] for k, v in p["rag"]["signals"].items()},
        })
    summary_path = week_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nSummary saved: {summary_path}")

    if args.schedule:
        print("Schedule mode: run complete. Add this command to cron for weekly execution.")


if __name__ == "__main__":
    main()
