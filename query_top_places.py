import os
import json
import uuid
from flask import Flask, request, jsonify, render_template
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cosmos DB configuration
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
COSMOS_KEY = os.environ.get("COSMOS_KEY")
DATABASE_NAME = os.environ.get("COSMOS_DATABASE", "MyDatabase")
CONTAINER_NAME = os.environ.get("COSMOS_CONTAINER", "MyContainer")

if not (COSMOS_ENDPOINT and COSMOS_KEY):
    raise Exception("COSMOS_ENDPOINT and COSMOS_KEY must be set in environment variables.")

client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

try:
    # Confirm container exists
    container.read()
except exceptions.CosmosResourceNotFoundError:
    raise Exception(f"Container '{CONTAINER_NAME}' not found in database '{DATABASE_NAME}'. Please verify that the resource exists.")

app = Flask(__name__)

# Serve the HTML page
@app.route('/')
def serve_html():
    api_key = os.getenv("AZURE_MAP_API")
    return render_template('InteractiveMap.html', api_key=api_key)

# New endpoint: Accepts user_address and user_filter from HTML, saves them, and runs a query.
@app.route('/query_and_save', methods=['POST'])
def query_and_save():
    data = request.get_json()
    user_address = data.get('user_address', '').strip()
    user_filter = data.get('user_filter', '').strip()
    
    if not user_address:
        return jsonify({"error": "Address is required."}), 400

    # Save the user input into Cosmos DB for logging or tracking
    document = {
        'id': str(uuid.uuid4()),
        'user_address': user_address,
        'user_filter': user_filter,
        'type': 'user_query'
    }
    try:
        container.create_item(document)
    except Exception as e:
        # Log the error if needed, but continue to query even if saving fails
        print("Error saving user input:", e)

    # Define fixed amenity categories
    amenity_categories = ["attraction", "hotel", "restaurant"]
    # Include the user-provided filter if present
    if user_filter:
        amenity_categories.append(user_filter)

    # Build the IN clause for the query
    amenities_clause = ", ".join([f"'{amenity}'" for amenity in amenity_categories])

    # Construct the query to find the top 7 places with matching amenity types and address
    query = (
        f"SELECT TOP 7 * FROM c "
        f"WHERE c.amenity_type IN ({amenities_clause}) "
        f"AND CONTAINS(c.address, '{user_address}') "
        f"ORDER BY c.rating DESC"
    )

    try:
        results = list(container.query_items(query=query, enable_cross_partition_query=True))
    except Exception as e:
        return jsonify({"error": f"Error executing query: {e}"}), 500

    return jsonify({"message": "Query successful", "results": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
