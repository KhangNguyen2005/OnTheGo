import os
import json
import argparse
from dotenv import load_dotenv
from openai import AzureOpenAI

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

    # Prepare the chat messages in the required format.
    messages = [
        {"role": "user", "content": query}
    ]

    # Generate the chat completion using the deployment name as the model.
    completion = client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_tokens=8000,
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
        return completion.to_json()

if __name__ == "__main__":
    # Parse command-line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query", 
        help=(
            "Pass the query to test the chat model. For example: "
            "'Give me recommendations from the restaurant data.'"
        ), 
        type=str
    )
    parser.add_argument("--stream", help="Stream the output", action="store_true")
    args = parser.parse_args()

    # If query is not provided, prompt the user.
    if args.query:
        query = args.query
    else:
        query = input("Please enter your query: ")

    # 1. Load the JSON file contents
    try:
        with open("restaurant.json", "r", encoding="utf-8") as f:
            restaurant_data = json.load(f)
        # Convert it to text
        restaurant_text = json.dumps(restaurant_data, indent=2)
    except FileNotFoundError:
        # If for some reason the file doesn't exist, handle gracefully
        restaurant_text = "No restaurant.json data found."

    # 2. Append the JSON data to the query
    query_with_json = (
        f"Below is the content of restaurant.json:\n\n"
        f"{restaurant_text}\n\n"
        f"User's request: {query}"
    )

    # 3. Invoke the AI with the combined query
    response = invoke_ai(query_with_json, stream=args.stream)

    if not args.stream:
        print(response)
