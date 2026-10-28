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

    # response = client.responses.create(model= model,
    #                         instructions= instruction,
    #                         input= query,
    #                         tools=[
    #                             {
    #                              "type" :"web_search"
    #                         },
    #                         ],
    #                         tool_choice= "required")

    llm = AzureChatOpenAI(
        azure_endpoint= api_endpoint,
        api_key=api_key,
        api_version=api_version,
        model=model
    )

    prompt_template = ChatPromptTemplate.from_messages([{'role': 'system','content': instruction},{'role':"user",'content': query}])
    prompt = prompt_template.format_messages(instruction= instruction,
                                             query= query)
    response = llm.invoke(prompt    )
    # print("response: /n ", response)
    # result = response.output_text
    result = response.content
    
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
    
        Write the report in Markdown with these sections:
        - Executive Summary
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

        report = query_llm(instructions,question)

        report_path.write_text(report,encoding="utf-8")

        print(f"/n report saved in file {report_path}")
    except Exception as e:
        print("found error", e)

def main():
    simple_research()

main()
    



#reseaech-? gather quetion, plan research task-> gather info , evidence-> analyse data-> first draft,review->