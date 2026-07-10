# Project Health Reporting Agent

Automated project health reporting for Professional Services teams. Determines RAG (Red/Amber/Green) status from Excel project plans and generates reports via CLI, web UI, or an interactive chat agent.

**Try the live demo:** [https://project-health-agent.vercel.app/](https://project-health-agent.vercel.app/)

---

## Quick Start

```bash
# 1. Clone
git clone <repo-url>
cd project-health-agent

# 2. Install dependencies
uv sync

# 3. Run CLI batch (processes sample data)
uv run python run.py

# 4. Run web UI
uv run python app.py
# Opens at http://localhost:8005
```

### Prerequisites

- Python 3.11 – 3.12
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

### Usage modes

| Mode | Command | Description |
|---|---|---|
| Web UI | `uv run python app.py` | Upload Excel → RAG assessment + chat agent |
| CLI batch | `uv run python run.py` | Process `data/*.xlsx` → Markdown + JSON reports |
| CLI agent | `uv run python agent.py` | Interactive LangChain/Groq agent |
| PPTX report | `uv run python monthly_synthesis.py` | Monthly executive deck from weekly data |
| Cron | `0 9 * * 1 uv run python run.py --schedule` | Weekly automated run |

> **Note:** The LLM agent (chat + `agent.py`) requires a [Groq API key](https://console.groq.com/keys). Set it in `.env`: `GROQ_API_KEY=your_key_here`. The CLI runner and RAG engine work without one.
