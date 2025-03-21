import os
import json
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

# Explicitly load the .env file (adjust the path if needed)
load_dotenv(dotenv_path=".env")

endpoint = "https://onthego.documents.azure.com:443/"
key = os.getenv("COSMOS_DB_KEY")

# Debug: Print the key to confirm it's loaded (remove in production)
if key is None:
    raise ValueError("COSMOS_DB_KEY not found. Make sure your .env file is in the correct location.")
else:
    print("COSMOS_DB_KEY loaded successfully.")

client = CosmosClient(endpoint, key)

database_name = 'MyDatabase'
container_name = 'MyContainer'

# Create or get your database
database = client.create_database_if_not_exists(id=database_name)

# Create or get your container
container = database.create_container_if_not_exists(
    id=container_name,
    partition_key=PartitionKey(path="/amenity_type")
)

# Map each file to an amenity_type
json_files = {
    "restaurant.json": "restaurant",
    "hotel.json": "hotel",
    "attraction.json": "attraction",
    "location.json": "location",
    "result.json": "result"
}

for file_name, amenity_type in json_files.items():
    if not os.path.exists(file_name):
        print(f"Skipping {file_name}; it does not exist.")
        continue

    with open(file_name, "r", encoding="utf-8") as f:
        file_content = json.load(f)

    doc = {
        "id": file_name,
        "content": file_content,
        "amenity_type": amenity_type
    }

    container.create_item(body=doc)
    print(f"Uploaded {file_name} as a single document with amenity_type '{amenity_type}'.")

print("All JSON files have been processed as single documents.")
