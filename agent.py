import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent

load_dotenv()

from tools.analyze import analyze_project


def create_project_agent():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None, "GROQ_API_KEY not set"

    model = ChatGroq(model="llama-3.3-70b-versatile")
    agent = create_agent(
        model=model,
        tools=[analyze_project],
        system_prompt="""You are a project health reporting agent. Your only job is to call analyze_project with the file path and report back the EXACT results from that tool. Do NOT generate your own assessment or use general knowledge — the tool output is the single source of truth.

Rules:
1. Always call analyze_project first. Never answer from memory.
2. Report the signal-level breakdown exactly as the tool returned it — status per signal, with the reason given by the tool.
3. When asked about a specific signal, quote the tool's finding for that signal.
4. If the tool says "insufficient_data", say that — do not guess.
5. Keep it concise but complete: include the overall RAG, each signal's status, and the tool's specific reason for each.""",
    )
    return agent, None


if __name__ == "__main__":
    agent, err = create_project_agent()
    if err:
        print("Error:", err)
        sys.exit(1)

    print("Project Health Agent ready. Type your query (or 'q' to quit).")
    while True:
        user_query = input("User: ")
        if user_query.strip().lower() in ("q", "\\q", "quit", "exit"):
            print("Exiting agent mode.")
            break
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_query}]},
            config={"configurable": {"thread_id": "user-123"}},
        )
        print(result["messages"][-1].content)
