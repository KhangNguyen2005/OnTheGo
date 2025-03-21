import os
import json
from azure.cosmos import CosmosClient, PartitionKey

# Replace with your Cosmos DB account details
endpoint = "https://onthego.documents.azure.com:443/"
key = "dpffk2Istd32WAgZh39MqQ8ZV4X3DF0kW9FV6z4gdeFXScIhLqsHGCLbw8ODdE7Fs9KYZkGe0gPhACDbSTMRCg=="
client = CosmosClient(endpoint, key)

database_name = 'MyDatabase'
container_name = 'MyContainer'

# Create or get your database
database = client.create_database_if_not_exists(id=database_name)

# Create or get your container
# We'll use '/amenity_type' as the partition key so we can easily query by type
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

    # Read the entire JSON file
    with open(file_name, "r", encoding="utf-8") as f:
        file_content = json.load(f)

    # Construct one document that contains all the data from this file
    doc = {
        # 'id' must be unique in Cosmos DB; here we just use the file name
        "id": file_name,
        # We'll store the entire JSON data under "content"
        "content": file_content,
        # Our partition key
        "amenity_type": amenity_type
    }

    # Create (or upsert) the document in Cosmos DB
    container.create_item(body=doc)
    print(f"Uploaded {file_name} as a single document with amenity_type '{amenity_type}'.")

print("All JSON files have been processed as single documents.")