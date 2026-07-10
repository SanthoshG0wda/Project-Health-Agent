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
        system_prompt="""You are a project health reporting agent. Answer in one short sentence or less. Never repeat the full assessment — the user already sees it in the UI. If asked for status, reply with just the color word and one reason. No preamble.""",
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
