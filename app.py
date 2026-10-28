from agent.planner import plan_research
from agent.researcher import research_topic
from agent.orchestrator import run_research, run_demo_research


def main():
    query = input("Enter topic to research")
    tasks = plan_research(query)

    research_result = []
    for task in tasks:
        result = research_topic(task)
        research_result.append(result)
        print(f"summary of task added: {result.summary} \n")

def call_orchestrator():
    run_demo_research()

if __name__ == "__main__":
    call_orchestrator()
