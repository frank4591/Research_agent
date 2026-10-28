# Its function should accept one subquestion and return structured research findings, including a summary and source references.


import json
import os

from dotenv import load_dotenv
from pydantic import BaseModel,Field
from openai import AzureOpenAI
from retyr_utils import retry_azure_call
from llm.aure_llm import LLMClient
import logging
import time
from usage_tracker import usage_tracker
from citation_validator import validate_source_urls

logger = logging.getLogger(__name__)


# from pydantic import BaseModel, Field, HttpUrl

load_dotenv()

class SourceReference(BaseModel):
    title: str = Field(description="Title of the source")
    url: str = Field(description="URL of the source")
    relevance: str = Field(
        description="What this source contributes to the research"
    )


class ResearchData(BaseModel):
    research_findings: str = Field(
        description="Evidence and findings relevant to the research task"
    )
    summary: str = Field(
        description="Concise summary of the findings"
    )
    sources: list[SourceReference] = Field(
        description="Sources actually used to support the findings"
    )
    limitations: list[str] = Field(
        description="Evidence gaps or uncertainties"
    )

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

# def research_topic(query)-> ResearchData:

#     instructions = """
#          You are a rigorous research analyst. Produce evidence-backed,
#             balanced, and actionable research reports.
        
#             Research objectives:
#             1. Break the user's question into its main research dimensions.
#             2. Use web search to find relevant, trustworthy, and current evidence.
#             3. Prioritize official documentation, primary sources, and original research.
#             4. Compare findings across multiple independent sources when possible.
#             5. Distinguish verified facts, source claims, and your own analysis.
#             6. Never invent facts, quotations, citations, or URLs.
#             7. Highlight conflicting evidence, missing information, and uncertainty.
#             8. Evaluate options against explicit criteria relevant to the question.
#             9. Make recommendations supported by evidence and explain trade-offs.
#             10. State when evidence is insufficient to reach a confident conclusion.
        
#     Output the answer in structured format object
#     """
#     response = client.chat.completions.parse(
#         model=MODEL,
#         messages= [
#             {"role": "system", "content": instructions},
#                         {"role": "user", "content": query},
#         ],
#         response_format=ResearchData,
#     )
#     print(f"response: {response.choices[0].message.content}")
#     if not response.choices:
#         raise ValueError("The API returned no completion choices")

#     choice = response.choices[0]
#     message = choice.message

#     if message.refusal:
#         raise ValueError(f"Research request was refused: {message.refusal}")

#     if message.parsed is None:
#         raise ValueError(
#             f"No structured research data was returned "
#             f"(finish_reason={choice.finish_reason})"
#         )

#     return message.parsed


def structure_findings(query: str) -> ResearchData:
    """Structure research information supplied in the query."""

    if not query.strip():
        raise ValueError("Research query cannot be empty.")

    instructions = """
    You are a rigorous research analyst.

    Analyze the research information provided by the user.
    Do not claim to have performed web searches.

    Separate evidence from interpretation.
    Identify uncertainty and missing evidence.
    Only include source URLs that were provided in the input.
    If no sources were provided, return an empty sources list.

    Return structured findings, a concise summary, sources,
    and limitations.
    """

# changing to retry function using tenacity
    # response = client.chat.completions.parse(
    #     model=MODEL,
    #     messages=[
    #         {"role": "system", "content": instructions},
    #         {"role": "user", "content": query},
    #     ],``
    #     tools=[{"type":"web_search"}]
    #     tool_choice="required",
    #     response_format=ResearchData,
    # )
    client = LLMClient.get_client()
    response = retry_azure_call(
        client.responses.parse,
        model = LLMClient.get_model(),
        instructions=instructions,
        input=query,
        tools=[{"type": "web_search"}],
        tool_choice="required",
        text_format=ResearchData,
    )

    result = response.output_parsed
    if result is None:
        raise ValueError("The API did not return structured research data.")

    # print(f"Token usage: {response.usage}")

    return result

# structure_findings("What are the core features and functionalities of LangGraph, CrewAI, and AutoGen for AI agent development?")


def research_topic(query: str) -> ResearchData:
    """
    Search the web and return structured research findings.
    """

    if not query.strip():
        raise ValueError("Research query cannot be empty.")

    instructions = """
    You are a rigorous research analyst.

    Investigate the user's research question using web search.

    Requirements:
    1. Search for current, relevant evidence.
    2. Prefer official documentation and primary sources.
    3. Explain the findings clearly and objectively.
    4. Distinguish established facts from interpretation.
    5. Identify conflicting evidence and missing information.
    6. Never invent facts or claim that an unverified source
       supports a statement.
    7. Return a concise summary and detailed findings.

    The application will collect actual source citations from
    the web-search response. Do not invent source URLs.

    Return structured output matching the ResearchData schema.
    """
    client = LLMClient.get_client()
    started = time.perf_counter()

    logger.info(
        "Research started",
        extra={
            "component": "researcher",
            "query": query,
        },
    )
    
    response = retry_azure_call(
        client.responses.parse,
        model=LLMClient.get_model(),
        instructions=instructions,
        input=query,
        tools=[{"type": "web_search"}],
        tool_choice="required",
        text_format=ResearchData,
    )

    usage_tracker.record("researcher", response)

    # Verify that the hosted web-search tool actually ran.
    search_was_used = any(
        item.type == "web_search_call"
        for item in response.output
    )

    if not search_was_used:
        raise RuntimeError(
            "The response did not contain a web-search call."
        )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "The API did not return parsed ResearchData."
        )

    logger.info(
    "Research completed",
    extra={
        "component": "researcher",
        "source_count": len(result.sources),
        "duration_seconds": round(
            time.perf_counter() - started, 3
                ),
            },
        )

    # Collect URLs supplied by the actual web-search citations.
    verified_sources = []
    seen_urls = set()

    for item in response.output:
        if item.type != "message":
            continue

        for content in item.content:
            if content.type != "output_text":
                continue

            for annotation in content.annotations:
                if annotation.type != "url_citation":
                    continue

                url = annotation.url

                if url in seen_urls:
                    continue

                seen_urls.add(url)

                verified_sources.append(
                    SourceReference(
                        title=annotation.title or url,
                        url=url,
                        relevance=(
                            "Cited in the web-grounded response"
                        ),
                    )
                )

    # Do not silently treat model-generated URLs as verified.
    # result.sources = verified_sources

    # if not result.sources:
    #     print(
    #         "Warning: No URL citation annotations were found. "
    #         "Inspect the raw response before trusting the report."
    #     )

    
    result.sources, url_issues = validate_source_urls(
        verified_sources
    )

    if url_issues:
        logger.warning(
            "Some collected citations were rejected",
            extra={
                "component": "researcher",
                "rejected_source_count": len(url_issues),
            },
        )

    if not result.sources:
        logger.warning(
            "No valid source citations were collected",
            extra={"component": "researcher"},
        )


    # print(f"Web search used: {search_was_used}")
    # print(f"Sources cited: {len(result.sources)}")
    # print(f"Token usage: {response.usage}")

    return result


def research():
    research = research_topic(
    "What are the core features of LangGraph, CrewAI, "
    "and AutoGen for AI agent development? Prioritize "
    "official documentation and compare workflow control."
)

    print("\nSUMMARY\n")
    print(research.summary)

    print("\nFINDINGS\n")
    print(research.research_findings)

    print("\nSOURCES\n")
    for source in research.sources:
        print(f"- {source.title}: {source.url}")

    print("\nLIMITATIONS\n")
    for limitation in research.limitations:
        print(f"- {limitation}")

# research()

# if __name__ == "__main__":
#     research = research_topic(
#         "What are the core features of LangGraph, CrewAI, "
#         "and AutoGen for AI agent development? Prioritize "
#         "official documentation and compare workflow control."
#     )

#     print("\nSUMMARY\n")
#     print(research.summary)

#     print("\nFINDINGS\n")
#     print(research.research_findings)

#     print("\nSOURCES\n")
#     for source in research.sources:
#         print(f"- {source.title}: {source.url}")

#     print("\nLIMITATIONS\n")
#     for limitation in research.limitations:
#         print(f"- {limitation}")
