import os
import json
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

# Load environment variables from .env file (make sure COSMOS_DB_KEY is defined)
load_dotenv(dotenv_path=".env")

# Define your Cosmos DB endpoint and key
endpoint = "https://onthego.documents.azure.com:443/"
key = os.getenv("COSMOS_DB_KEY")
client = CosmosClient(endpoint, key)

# Set your database and container names
database_name = "MyDatabase"    # Adjust if needed
container_name = "MyContainer"  # Adjust if needed

# Create the database if it doesn't exist
database = client.create_database_if_not_exists(id=database_name)

# Create the container if it doesn't exist with a partition key on "/amenity_type"
container = database.create_container_if_not_exists(
    id=container_name,
    partition_key=PartitionKey(path="/amenity_type")
)

# Map each JSON file to its corresponding amenity type.
json_files = {
    "hotel.json": "accommodation",
    "restaurant.json": "restaurant",
    "attraction.json": "attraction",
    "location.json": "location",
    "result.json": "result"
}

# Log which files are detected in the current directory
files_in_dir = os.listdir(".")
print("Files in current directory:", files_in_dir)

# Process each file and insert or update every document into Cosmos DB
for file_name, amenity_type in json_files.items():
    if not os.path.exists(file_name):
        print(f"Skipping {file_name} because it does not exist.")
        continue

    print(f"Processing {file_name} as '{amenity_type}'...")
    with open(file_name, "r", encoding="utf-8") as f:
        try:
            documents = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in {file_name}: {e}")
            continue

    count = 0
    for doc in documents:
        # Add the amenity_type property
        doc["amenity_type"] = amenity_type

        # Generate a unique 'id' if not already present (using the Name field and amenity type)
        if "id" not in doc:
            if "Name" in doc:
                doc["id"] = (amenity_type + "_" + doc["Name"]).replace(" ", "_")
            else:
                doc["id"] = f"{amenity_type}_{count}"

        try:
            # Use upsert_item to avoid duplicate errors
            container.upsert_item(body=doc)
            count += 1
        except Exception as e:
            print(f"Failed to upsert document {doc.get('id', 'unknown')}: {e}")

    print(f"Processed {count} items from {file_name} as '{amenity_type}'.")

print("All JSON files processed successfully!")
