#[x] Exercise 1: Change the research style

# Modify the instructions so the agent must include a comparison table and a recommendation for a startup with a two-person engineering team.

# [x] Exercise 2: Add input validation

# Reject questions shorter than 10 characters before calling the API. Why is it useful to validate input before making a paid API request?

# [x] Exercise 3: Inspect the response

# Print response.usage after the API call. What can token usage tell you about the cost of a research run, and what other costs might need to be measured?


import os 
from pathlib import Path

from dotenv import load_dotenv
from openai import AzureOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()
api_endpoint = os.environ['AZURE_GPT_4o_ENDPOINT'] = os.getenv('AZURE_GPT_4o_ENDPOINT') if os.getenv('AZURE_GPT_4o_ENDPOINT') else input("enter azure api endpoint")
api_key = os.environ['AZURE_OPENAI_API_KEY'] = os.getenv('AZURE_OPENAI_API_KEY') if os.getenv('AZURE_OPENAI_API_KEY') else input("enter azure api key",)
model = os.environ['AZURE_OPENAI_MODEL_NAME'] = os.getenv('AZURE_OPENAI_MODEL_NAME') or input("enter azure model name")
deployment_name = os.environ['AZURE_OPENAI_MODE_DEPOYMENT_NAME'] = os.getenv('AZURE_OPENAI_MODE_DEPOYMENT_NAME') or input("enter azure deploymentname")
api_version = os.environ['AZURE_OPENAI_API_VERSION'] = os.getenv('AZURE_OPENAI_API_VERSION') or input("enter azure api version")


def query_llm(instruction,query):
    client = AzureOpenAI(
        azure_endpoint= api_endpoint,
        api_key= api_key,
        api_version= api_version,
        
    )

    response = client.responses.create(model= model,
                            instructions= instruction,
                            input= query,
                            tools=[
                                {
                                 "type" :"web_search"
                            },
                            ],
                            tool_choice= "required")

    result = response.output_text
    print(f"response token usage: { response.usage}")
    
    return result

def simple_research():
    instructions = """
       You are a rigorous research analyst. Produce evidence-backed,
    balanced, and actionable research reports.

    Research objectives:
    1. Break the user's question into its main research dimensions.
    2. Use web search to find relevant, trustworthy, and current evidence.
    3. Prioritize official documentation, primary sources, and original research.
    4. Compare findings across multiple independent sources when possible.
    5. Distinguish verified facts, source claims, and your own analysis.
    6. Never invent facts, quotations, citations, or URLs.
    7. Highlight conflicting evidence, missing information, and uncertainty.
    8. Evaluate options against explicit criteria relevant to the question.
    9. Make recommendations supported by evidence and explain trade-offs.
    10. State when evidence is insufficient to reach a confident conclusion.

    For comparisons:
    - Use consistent criteria across all options.
    - Distinguish documented features from qualitative judgments.
    - Explain important advantages, limitations, and trade-offs.
    - Avoid declaring a universal winner when the best choice depends
    on the user's requirements.

    Output format: Markdown
    ## 1. Executive Summary
    Summarize the question, major findings, and conclusion.

    ## 2. Comparison Table
    Compare the options against relevant criteria.
    Include evidence-backed observations and meaningful trade-offs.

    ## 3. Key Findings
    Present the most important findings as numbered points.

    ## 4. Evidence and Analysis
    Explain the reasoning behind the comparison.
    Include citations close to the claims they support.

    ## 5. Recommendation
    Recommend the best-fit option for the stated requirements.
    Explain why, when alternatives are preferable, and what assumptions
    the recommendation depends on.

    ## 6. Limitations and Uncertainties
    Identify evidence gaps, conflicting information, and limitations.

    ## 7. Sources
    List the sources used, with descriptive titles and working URLs.
    Prefer primary sources and indicate publication dates when available.

    Maintain a neutral tone. Do not confuse popularity with suitability.
    Do not make unsupported claims about future performance or trends."""
    
    question = input("Enter the quesiton to research: ")

    try:

        print("researching ...please wait..")

        file_path = Path("./output")
        Path.mkdir(file_path,parents=True,exist_ok=True)
        report_path = file_path/"research_report.md"

        if input_validated(question):
            print("validated input")
            report = query_llm(instructions,question)
        else:
            raise StringLengthError("Legnth of query is less than 10 character.please correct")
        report_path.write_text(report,encoding="utf-8")

        print(f"/n report saved in file {report_path}")
    except Exception or StringLengthError as e:
        print("found error", e)

class StringLengthError(ValueError):

    def __int__(self, message="length of query is small"):
        self.message = message
        super().__init__(self.message)

def input_validated(query: str):
    return (True if len(query) > 10 else False)

def main():
    simple_research()

main()
    



#reseaech-? gather quetion, plan research task-> gather info , evidence-> analyse data-> first draft,review->