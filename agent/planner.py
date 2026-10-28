
import json
import os

from dotenv import load_dotenv
from openai import AzureOpenAI
from retyr_utils import retry_azure_call
from llm.aure_llm import LLMClient 
import logging
import time
from usage_tracker import usage_tracker

logger = logging.getLogger(__name__)

load_dotenv()


def create_client() -> AzureOpenAI:
    """Create an Azure OpenAI client from environment variables."""

    required_vars = [
        "AZURE_GPT_4o_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION",
    ]

    missing = [name for name in required_vars if not os.getenv(name)]
    if missing:
        raise ValueError(
            f"Missing environment variables: {', '.join(missing)}"
        )

    return AzureOpenAI(
        azure_endpoint=os.environ["AZURE_GPT_4o_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    )


client = create_client()

# This must be your Azure deployment name, not necessarily
# the underlying model's public model name.
MODEL = os.getenv("AZURE_OPENAI_MODEL_NAME")


def validate_tasks(data: object) -> list[str]:
    """Validate the parsed planner output."""

    if not isinstance(data, dict):
        raise ValueError("Planner output must be a JSON object.")

    tasks = data.get("tasks")

    if not isinstance(tasks, list) or not 3 <= len(tasks) <= 5:
        raise ValueError("Planner must return 3–5 research tasks.")

    if not all(
        isinstance(task, str) and task.strip()
        for task in tasks
    ):
        raise ValueError("Every research task must be a non-empty string.")

    return [task.strip() for task in tasks]


def plan_research(question: str) -> list[str]:
    """
    Decompose a research question into 3–5 focused subquestions.
    Planning only: no web search or evidence gathering.
    """

    if not question.strip():
        raise ValueError("Research question cannot be empty.")

    if not MODEL:
        raise ValueError("AZURE_OPENAI_MODEL_NAME is not configured.")

    instructions = """
    You are a research planning assistant.

    Your task is to decompose the user's research question into
    3 to 5 focused, non-overlapping research subquestions.

    Requirements:
    - Cover the main dimensions needed to answer the question.
    - Make each task specific and independently researchable.
    - Avoid duplicate or overly broad tasks.
    - Order tasks logically.
    - Do not answer the research question.
    - Do not perform web searches or gather evidence.

    Return a JSON object with one key, "tasks".
    Its value must be an array containing 3 to 5 strings.
    """

    # response = client.chat.completions.create(
    #     model=MODEL,
    #     messages=[
    #         {"role": "system", "content": instructions},
    #         {"role": "user", "content": question},
    #     ],
    #     response_format={"type": "json_object"},
    #     temperature=0.2,
    # )
    started = time.perf_counter()
    client = LLMClient.get_client()
    
    logger.info(
    "Planning started",
    extra={"component": "planner"}    )   

   
    try:
        response = retry_azure_call(
            client.responses.create,
            model=LLMClient.get_model(),
            instructions=instructions,
            input=(
                f"Research question: {question}\n"
                'Return a JSON object with a "tasks" array of 3 to 5 strings.'
            ),
            text={"format": {"type": "json_object"}},
        )

        usage_tracker.record("planner", response)
        # Keep your existing JSON parsing and task validation here.
        content = response.output_text

        # ... your existing validation code ...
        if not content:
            raise ValueError("Planner returned an empty response.")
    
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Planner returned invalid JSON.") from exc

        tasks = validate_tasks(parsed)

        # print(f"Generated {len(tasks)} research tasks.")
        # print(f"Token usage: {response.usage}")

        logger.info(
            "Planning completed",
            extra={
                "component": "planner",
                "task_count": len(tasks),
                "duration_seconds": round(
                    time.perf_counter() - started, 3
                ),
            },
        )

        return tasks

    except Exception:
        logger.exception(
            "Planning failed",
            extra={
                "component": "planner",
                "duration_seconds": round(
                    time.perf_counter() - started, 3
                ),
            },
        )
        raise

        


if __name__ == "__main__":
    question = (
        "Compare LangGraph, CrewAI, and AutoGen for "
        "production AI agent development."
    )

    for index, task in enumerate(plan_research(question), start=1):
        print(f"{index}. {task}")
