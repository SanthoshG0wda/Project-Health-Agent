# RAG Methodology — Project Health Reporting Agent

## Signals & Scoring

| Signal | Data Source | Green | Amber | Red |
|---|---|---|---|---|
| **Schedule Slippage** | Per-task "Schedule Health" field | ≤5% of tasks Red | 5–15% of tasks Red | >15% of tasks Red |
| **Budget Burn** | Budget total vs. spent vs. % complete | Burn ratio ≤1.10 | Burn ratio 1.11–1.25 | Burn ratio >1.25 |
| **Milestone Health** | Tasks past End Date, not Completed | ≤5 overdue | 6–15 overdue | >15 overdue |
| **Blockers** | Overdue tasks flagged Critical | 0 overdue critical | 1–2 overdue critical | >2 overdue critical |
| **Stakeholder Sentiment** | PM status comments (narrative) | Positive | Neutral / mixed | Negative |

## Aggregation Rule

- Each signal is scored independently (Green=0, Amber=1, Red=2).
- **Overall = worst individual signal**, with one exception:
  - If **exactly one** signal is Red and **all others with data** are Green → cap at **Amber**.
- If no data is available for a signal, it is excluded (does not drive the overall).

## Assumptions

1. **No explicit budget fields** exist in the current export format → budget is always `insufficient_data` until a source field is added.
2. **No explicit blocker field** exists → overdue Critical tasks serve as a proxy.
3. **No structured sentiment field** exists → sentiment is narrative-only and currently disabled.
4. The task-level "Schedule Health" field (with "Yellow" normalized to "Amber") is the primary schedule signal.
5. The "Critical ?" boolean column on tasks is used as the blocker proxy.
6. All dates are evaluated against the current date at analysis time.

## RAG Meaning

- **Green** — On track; no intervention needed.
- **Amber** — Some signals flagging; monitor and plan corrective actions.
- **Red** — Multiple signals critical; escalation required.
- **insufficient_data** — Not enough information to score; treat as Amber until data is provided.
