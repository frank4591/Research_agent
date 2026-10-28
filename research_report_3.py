#separate planning, execution, and evaluation into explicit Python functions.

# def plan_research(question):
#     # Break the question into focused subquestions
#     ...

# def search_subquestion(subquestion):
#     # Execute a search and collect evidence
#     ...

# def synthesize_findings(question, evidence):
#     # Combine findings into a report
#     ...

# def evaluate_report(question, report):
#     # Identify missing evidence and weak claims
#     ...


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
        You are a careful research assistant.
    
        Research the user's question using web search.
    
        Requirements:
        1. Identify the main aspects of the question.
        2. Search for relevant, trustworthy evidence.
        3. Prefer official documentation and primary sources.
        4. Distinguish verified facts from opinions or uncertainty.
        5. Cite sources using the citations provided by web search.
        6. Do not invent facts, quotations, or URLs.
        7. Compare evidences for multiple research answers
        8. Generate Recommendation from the provided evidences and research
    
        Write the report in Markdown with these sections:
        - Executive Summary
        - Comparision table of recommendations
        - Recommendation
        - Key Findings
        - Evidence and Analysis
        - Limitations and Uncertainties
        - Sources
        """
    
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



def plan_research(question):
    # Break the question into focused subquestions
    instructions = """
            You are a careful research assistant.
        
            Research the user's question using web search.
            Break the question into multiple questions, break it into 
            different submodule if required
        """


def main():
    simple_research()

main()
    



#reseaech-? gather quetion, plan research task-> gather info , evidence-> analyse data-> first draft,review->