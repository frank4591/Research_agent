#Step 4 — Build the synthesizer
# Once the above works, Step 3 — Add failure handling to the orchestrator ,
# the next component is agent/synthesizer.py. Its job is different from the researcher's: the researcher investigates one question, while the synthesizer compares evidence across all successful research tasks and produces one coherent report.

# Your synthesizer should:
# - Combine overlapping findings without repeating them.
# - Compare approaches using evidence from the collected research.
# - Identify disagreements, missing evidence, and limitations.
# - Preserve source titles and URLs.
# - Make recommendations that follow from the evidence, rather than inventing unsupported claims.

#Step 1 — Define the synthesizer's input and output
# Compare · Deduplicate · Evaluate evidence · Identify gaps



import json
from pathlib import Path

from pydantic import BaseModel, Field
from openai import APIError, AzureOpenAI
from usage_tracker import usage_tracker
from llm.aure_llm import LLMClient


# ---------- Structured output schemas ----------

class ReportSource(BaseModel):
    source_id: str
    title: str
    url: str


class ReportSection(BaseModel):
    heading: str
    content: str
    source_ids: list[str] = Field(
        description="IDs of supplied sources supporting this section"
    )


class Recommendation(BaseModel):
    recommendation: str
    rationale: str
    source_ids: list[str] = Field(
        description="IDs of supplied sources supporting this recommendation"
    )


class FinalReport(BaseModel):
    title: str
    executive_summary: str
    key_findings: list[str]
    sections: list[ReportSection]
    recommendations: list[Recommendation]
    evidence_gaps: list[str]
    limitations: list[str]


# ---------- Synthesis instructions ----------

SYNTHESIS_INSTRUCTIONS = """
You are a careful research analyst.

Your task is to synthesize supplied research results into a coherent,
evidence-based report answering the original research question.

Rules:
1. Use only the supplied research findings and source metadata.
2. Do not claim you independently verified a fact.
3. Do not invent facts, quotations, sources, URLs, or source IDs.
4. Compare findings across tasks and remove unnecessary repetition.
5. Identify disagreements, weak evidence, and missing information.
6. Recommendations must follow from the supplied evidence.
7. Use source IDs such as S1 and S2 to connect claims to sources.
8. Every section and recommendation should include relevant source IDs.
9. Only use source IDs that exist in the supplied source catalogue.
10. If evidence is insufficient, state that clearly.
11. Keep the report focused on the original question.
"""


# ---------- Convert research results to input data ----------

def prepare_research_context(
    successful_results: list,
    failed_tasks: list,
) -> tuple[str, list[ReportSource]]:

    source_catalogue = []
    source_ids_by_url = {}
    research_items = []

    for item in successful_results:
        result = item["result"]

        # Support Pydantic v2 objects returned by the research worker.
        result_data = result.model_dump(mode="json")

        validated_sources = []

        for source in result.sources:
            url = str(source.url)

            # Deduplicate sources by URL.
            if url not in source_ids_by_url:
                source_id = f"S{len(source_catalogue) + 1}"
                source_ids_by_url[url] = source_id

                source_catalogue.append(
                    ReportSource(
                        source_id=source_id,
                        title=source.title,
                        url=url,
                    )
                )

            source_id = source_ids_by_url[url]

            validated_sources.append({
                "source_id": source_id,
                "title": source.title,
                "url": url,
            })

        research_items.append({
            "task": item["task"],
            "research": result_data,
            "validated_sources": validated_sources,
        })

    context = {
        "research_results": research_items,
        "source_catalogue": [
            source.model_dump(mode="json")
            for source in source_catalogue
        ],
        "failed_tasks": failed_tasks,
    }

    return json.dumps(context, ensure_ascii=False), source_catalogue


# ---------- Main synthesizer ----------


def synthesize_research(
    question: str,
    research_context: str,
    source_catalogue: list[ReportSource],
    failed_tasks: list | None = None,
) -> FinalReport:

    if not research_context.strip():
        raise ValueError("Research context cannot be empty.")

    failed_tasks = failed_tasks or []

    prompt = f"""
Original research question:
{question}

Research context in JSON:
{research_context}

Failed tasks:
{json.dumps(failed_tasks, ensure_ascii=False)}

Produce the final report using the required structured schema.

Important:
- Use only source IDs in the supplied source catalogue.
- Include relevant source IDs in every section and recommendation.
- Account for failed research tasks when discussing coverage limitations.
- Do not treat a source's presence as proof that every claim is correct.
"""
    client = LLMClient.get_client()
    response = client.responses.parse(
        model = LLMClient.get_model(),
        instructions=SYNTHESIS_INSTRUCTIONS,
        input=prompt,
        text_format=FinalReport,
    )
    usage_tracker.record("researcher", response)

    report = response.output_parsed

    if report is None:
        raise RuntimeError("The model did not return a structured report.")

    valid_ids = {source.source_id for source in source_catalogue}

    for section in report.sections:
        unknown = set(section.source_ids) - valid_ids
        if unknown:
            raise ValueError(
                f"Section '{section.heading}' contains unknown "
                f"source IDs: {sorted(unknown)}"
            )

    for recommendation in report.recommendations:
        unknown = set(recommendation.source_ids) - valid_ids
        if unknown:
            raise ValueError(
                "Recommendation contains unknown source IDs: "
                f"{sorted(unknown)}"
            )

    return report


# ---------- Markdown report writer ----------

def save_report(
    report: FinalReport,
    source_catalogue: list[ReportSource],
    output_path: str = "research_report.md",
) -> Path:

    lines = [
        f"# {report.title}",
        "",
        "## Executive Summary",
        "",
        report.executive_summary,
        "",
        "## Key Findings",
        "",
    ]

    for finding in report.key_findings:
        lines.extend([f"- {finding}", ""])

    for section in report.sections:
        lines.extend([
            f"## {section.heading}",
            "",
            section.content,
        ])

        if section.source_ids:
            citations = " ".join(
                f"[{source_id}]"
                for source_id in section.source_ids
            )
            lines.extend(["", f"Sources: {citations}"])

        lines.append("")

    lines.extend(["## Recommendations", ""])

    for index, recommendation in enumerate(
        report.recommendations, start=1
    ):
        lines.extend([
            f"{index}. **{recommendation.recommendation}**",
            "",
            recommendation.rationale,
        ])

        if recommendation.source_ids:
            citations = " ".join(
                f"[{source_id}]"
                for source_id in recommendation.source_ids
            )
            lines.extend(["", f"Sources: {citations}"])

        lines.append("")

    lines.extend(["## Evidence Gaps", ""])

    for gap in report.evidence_gaps:
        lines.extend([f"- {gap}", ""])

    lines.extend(["## Limitations", ""])

    for limitation in report.limitations:
        lines.extend([f"- {limitation}", ""])

    lines.extend(["## Sources", ""])

    for source in source_catalogue:
        lines.append(
            f"- **[{source.source_id}] {source.title}** — {source.url}"
        )

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return destination
