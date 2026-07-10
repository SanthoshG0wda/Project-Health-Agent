import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent

load_dotenv()

from tools.analyze import analyze_project

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("Error: GROQ_API_KEY not found in .env file")
    sys.exit(1)

model = ChatGroq(model="llama-3.3-70b-versatile")

agent = create_agent(
    model=model,
    tools=[analyze_project],
    system_prompt="""You are a project health reporting agent for a Professional Services team.

When the user provides a file path, call the analyze_project tool with the file path.
Then present the results clearly to the user. Highlight the RAG status, key signals, and any recommendations.""",
)

if __name__ == "__main__":
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
