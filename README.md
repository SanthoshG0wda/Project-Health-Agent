# Project Health Reporting Agent

Automated project health reporting for Professional Services teams. Determines RAG (Red/Amber/Green) status from Excel project plans and generates weekly reports and monthly executive presentations.

## Design Decisions

**Deterministic RAG engine** — Scoring logic in `tools/rag_engine.py` with no LLM calls. Auditable, reproducible, explainable. Thresholds in `config/rag_thresholds.yaml`.

**5 signals scored independently** — Schedule slippage, budget burn, milestone health, blockers (via overdue critical tasks), stakeholder sentiment. Each outputs Green/Amber/Red or `insufficient_data`.

**Aggregation rule** — Overall = worst signal, except: if exactly one Red and all others Green, cap at Amber.

**Graceful degradation** — Missing data fields are tracked, not errored. Auto-detects different Excel formats.

## Usage

```bash
uv sync

# Batch run
uv run python run.py --date 2026-07-10

# Interactive AI agent
uv run python agent.py

# Monthly executive PPTX
uv run python monthly_synthesis.py

# Weekly cron
0 9 * * 1 cd /path/to/project && uv run python run.py --schedule
```

## Sample Results

| Project | RAG | Key Drivers |
|---|---|---|
| Zycus - UniSan S2P (Plan B) | Red | 54 overdue tasks, 3 critical overdue |
| Zycus - Titan S2P | Red | 33 overdue tasks, schedule at 5% Red |
| CRM Migration | Amber | Budget overrun (90% spent at 70% complete) |

See [RAG_METHODOLOGY.md](RAG_METHODOLOGY.md) for the full methodology.
