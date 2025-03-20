from llama_index.llms.azure_openai import AzureOpenAI
from dotenv import load_dotenv
from llama_index.experimental.query_engine import JSONalyzeQueryEngine
import os
import json

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

llm = AzureOpenAI (
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
    deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
    api_key = os.getenv("AZURE_OPENAI_API_KEY"),
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")    
)


with open('location.json', 'r') as f:
    list_of_locations = json.load(f)

engine = JSONalyzeQueryEngine(
    list_of_dict=list_of_locations,
    llm=llm,
    verbose=True
)

query = input("Please enter your query for the AI: ")
response = engine.query(query)