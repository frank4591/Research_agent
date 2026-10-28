
# Step 3 — Connect the synthesizer to your orchestrator

from pathlib import Path
import sys
import json
from usage_tracker import usage_tracker
from citation_validator import validate_report_source_ids

# Allow: python agent/main.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from agent.orchestrator import run_research

import logging

from agent.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

logger.info("Research agent starting")




from agent.orchestrator import run_research
from agent.synthesizer import (
    prepare_research_context,
    synthesize_research,
    save_report,
)


def main():
    question = (
        "Research production AI agents in 2026. "
        "Compare workflow control, reliability, and evaluation."
    )

    run = run_research(question)

    if not run["successful_results"]:
        print("No research succeeded. Cannot create a report.")
        return

    # Prepare context and source catalogue only once.
    research_context, source_catalogue = prepare_research_context(
        run["successful_results"],
        run["failed_tasks"],
    )

    # Synthesize using the prepared context.
    report = synthesize_research(
        question=question,
        research_context=research_context,
        source_catalogue=source_catalogue,
        failed_tasks=run["failed_tasks"],
    )

    #citation validation
    citation_issues = validate_report_source_ids(
    report,
    source_catalogue,
    )

    if citation_issues:
        raise ValueError(
            f"Report contains {len(citation_issues)} invalid source references."
        )
    
    # Reuse the same catalogue when saving.
    path = save_report(
        report,
        source_catalogue,
        output_path="outputs/research_report.md",
    )

    print(f"\nReport saved to: {path.resolve()}")
    print("\nExecutive Summary:\n")
    print(report.executive_summary)

    summary = usage_tracker.summary()

    logger.info(
        "Research run usage summary",
        extra={"usage_summary": summary},
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
