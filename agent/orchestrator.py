# the planner decides what to investigate, while each research worker investigates one specific topic. We keep these responsibilities separate so we can test and improve them independently.
# Step 1: Connect the planner to the research worker
#step2: Add failure handling to the orchestrator //make research_agent more error resilient
    # a) Because your planner returns list[str], we can simplify the loop and track successful and failed tasks separately.
    # b)  Later, we'll distinguish retryable API errors, such as rate limits and temporary server errors, from permanent errors, such as invalid configuration.
#strp3 :combine reult into one final report
# — Build the synthesizer-synthesizer compares evidence across all successful research tasks and produces one coherent report.
# Step 4 — Connect the synthesizer to your orchestrator

#step 6, - Error hanfling, failure handlaing, logging, output validation, observability
# Step	Improvement	What you'll learn
# 1	Bounded retries	Recover from temporary API failures without infinite loops , use tenacity for adding robust retry behaviors to functions, methods, and code blocks
# 2	Structured logging	Trace which research task ran, failed, or took too long
# 3	Token and cost tracking	Measure model usage and estimate API costs
# 4	Citation validation	Catch missing, malformed, and unsupported source references
# 5	Evaluation metrics	Measure research quality against repeatable test cases
# 
#step7- token usage tracking, Each component already receives an API response, so we'll record its usage immediately after the request succeeds.
#An orchestrator controls the workflow by passing each sub-question to a research worker, which uses web search to gather evidence and returns structured results using Pydantic models
#The orchestrator controls execution; the planner creates the tasks.
#the orchestrator is the control-flow mechanism. It determines which component runs, when it runs, and what happens when something fails.

from .planner import plan_research
from .researcher import research_topic
import logging
import time

logger = logging.getLogger(__name__)

def run_research(question:str):
    """plan research and investigate sub research"""

    print("\n[1/3] Planning research...")

    tasks = plan_research(question)

    if not tasks:
        raise ValueError("The planner returned no research tasks.")

    successful_results = []
    failed_tasks = []
    # research_result =[]

    print("\n[2/3] Researching each task...")

    for index , task in enumerate(tasks, start= 1):
        # print(f"\nResearch task {index}/{len(tasks)}")
        # print(f"Question: {task}")
        started = time.perf_counter()

        logger.info(
            "Research task started",
            extra={
                "component": "orchestrator",
                "task_number": index,
                "task": task,
            },
        )
        try:
            result = research_topic(task)

            successful_results.append({
                    "task": task,
                    "result": result,
                })
            
            logger.info(
                        "Research task completed",
                        extra={
                            "component": "orchestrator",
                            "task_number": index,
                            "duration_seconds": round(
                                time.perf_counter() - started, 3
                            ),
                        },
                    )
            # research_result.append(result)
            # print("Research completed.")
            print(f"Task {index} completed.")

        except Exception as exc:
            # Record the failure without losing previous results.
            failed_tasks.append({
                "task": task,
                "error": str(exc),
            })

            logger.exception(
            "Research task failed",
            extra={
                "component": "orchestrator",
                "task_number": index,
                "duration_seconds": round(
                    time.perf_counter() - started, 3
                ),
            },
        )

            # print(f"Task {index} failed: {exc}")

    # print("\n[3/3] Research collection complete.")
    print(
        f"\nResearch complete: {len(successful_results)} succeeded, "
        f"{len(failed_tasks)} failed."
    )
    return {
        "successful_results": successful_results,
        "failed_tasks": failed_tasks,
    }

    # return {
    #     "original_question": question,
    #     "tasks": tasks,
    #     "research_results": research_result,
    # }

def run_demo_research():
    question = (
        "How are production AI agents evolving in 2026? "
        # "Compare workflow control, reliability, and evaluation."
    )

    output = run_research(question)

    print("\n=== RESEARCH SUMMARY ===")

    for index, result in enumerate(
        output["research_results"], start=1
    ):
        print(f"\n--- Task {index} ---")
        print(result.summary)

if __name__ == "__main__":
    run_demo_research()