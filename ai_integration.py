import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

def invoke_ai(query: str, stream: bool = False):
    # Read configuration from environment variables.
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
    subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    # Initialize the Azure OpenAI client.
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=subscription_key,
        api_version=api_version,
    )

    # Load the JSON data
    with open("top_places_by_amenity.json", "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    # Convert JSON to string for context
    data_str = json.dumps(data, indent=2)

    # Messages for the model
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. You have access to the following JSON data:\n\n"
                f"{data_str}\n\n"
                "Only use this JSON data to answer the user's query. "
                "If the answer cannot be found in the data, respond with an appropriate message."
            )
        },
        {
            "role": "user",
            "content": query
        }
    ]

    # Generate chat completion
    completion = client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_tokens=3000,
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=stream
    )

    if stream:
        for chunk in completion:
            print(chunk)
    else:
        return completion.choices[0].message.content

if __name__ == "__main__":
    # Hard-coded query
    query = (
        "Generate an optimal travel plan based on all the JSON data to a JSON file. "
        "Include destination names, locations, top-rated amenities, and an ideal sequence for visiting them. "
        "Assume the traveler wants to minimize travel time while maximizing experience. Include morning , afternoon and evening activities."
    )

    # Call the function with the hardcoded query
    response = invoke_ai(query)
    print(response)
