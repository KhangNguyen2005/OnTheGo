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

    # --- Load your JSON file here ---
    with open("result.json", "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    # Convert JSON to a string for the prompt
    data_str = json.dumps(data, indent=2)

    # Prepare the chat messages in the required format.
    # You can place the data in a "system" message to instruct the model
    # to use only the provided data. Alternatively, you can place it in
    # a "user" message. This example uses a system message to set context.
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

    # Generate the chat completion using the deployment name as the model.
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
        return completion.to_json()

if __name__ == "__main__":
    # Parse command-line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query",
        help=(
            "Pass the query to test the chat model "
            "(e.g., 'Give me recommendation spots in California with location, name, "
            "price and ratings to a JSON file')"
        ),
        type=str
    )
    parser.add_argument("--stream", help="Stream the output", action="store_true")
    args = parser.parse_args()

    # If query is not provided as an argument, prompt the user.
    if args.query:
        query = args.query
    else:
        query = input("Please enter your query: ")

    response = invoke_ai(query, stream=args.stream)
    if not args.stream:
        print(response)