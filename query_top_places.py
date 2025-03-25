import sys
import os
import json
import time
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
COSMOS_DB_KEY = os.environ.get("COSMOS_DB_KEY")
DATABASE_NAME = os.environ.get("COSMOS_DATABASE", "MyDatabase")
CONTAINER_NAME = os.environ.get("COSMOS_CONTAINER", "MyContainer")

if not (COSMOS_ENDPOINT and COSMOS_DB_KEY):
    raise Exception("COSMOS_ENDPOINT and COSMOS_KEY must be set in environment variables.")

client = CosmosClient(COSMOS_ENDPOINT, COSMOS_DB_KEY)
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

try:
    # Confirm container exists
    container.read()
except exceptions.CosmosResourceNotFoundError:
    raise Exception(f"Container '{CONTAINER_NAME}' not found in database '{DATABASE_NAME}'. Please verify that the resource exists.")

# Query distinct amenity types from the database
distinct_query = "SELECT DISTINCT c.amenity_type FROM c"
try:
    distinct_result = list(container.query_items(query=distinct_query, enable_cross_partition_query=True))
except Exception as e:
    raise Exception(f"Error querying distinct amenities: {e}")

allowed_amenities = ["accomodation", "attraction", "location", "restaurant", "result"]

# Extract amenity types from results (filtering out empty values)
amenities = [
    item['amenity_type'] 
    for item in distinct_result 
    if 'amenity_type' in item and item['amenity_type']
]

# Filter to only use the five desired amenity types.
amenities = [amenity for amenity in amenities if amenity.lower() in allowed_amenities]

print(f"Distinct amenities found: {amenities}")

# Calculate timestamp for five minutes ago
five_minutes_ago = int(time.time()) - 300  # current time in seconds minus 180

final_results = {}
for amenity in amenities:
    query = (
        f"SELECT TOP 2 * FROM c "
        f"WHERE c.amenity_type = '{amenity}' "
        f"AND c._ts >= {five_minutes_ago} "  # using five minutes ago
        f"ORDER BY c._ts DESC"
    )
    try:
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
    except Exception as e:
        raise Exception(f"Error querying items for amenity '{amenity}': {e}")
    final_results[amenity] = items
    print(f"Found {len(items)} items for amenity '{amenity}'.")

# Save the combined results to a JSON file
output_file = "top_places_by_amenity.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_results, f, indent=4)

print(f"Query successful. Results saved to {output_file}")
