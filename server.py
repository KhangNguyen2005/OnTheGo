from flask import Flask, request, jsonify, render_template
import json
import subprocess
import os
import time
import sys
import traceback
import uuid
from dotenv import load_dotenv
from azure.cosmos import CosmosClient, exceptions

# Load environment variables
BASE_DIR = os.environ.get("MY_APP_BASE_DIR", os.path.abspath(os.path.dirname(__file__)))
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

# Cosmos DB configuration
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
    # Confirm the container exists
    container.read()
except exceptions.CosmosResourceNotFoundError:
    raise Exception(f"Container '{CONTAINER_NAME}' not found in database '{DATABASE_NAME}'. Please verify that the resource exists.")

app = Flask(__name__)

# File and script names using absolute paths.
FETCHING_DATA_SCRIPT = os.path.join(BASE_DIR, "fetching_data.py")
UPLOAD_COSMOS_SCRIPT = os.path.join(BASE_DIR, "upload_cosmos.py")
RESTAURANT_JSON = os.path.join(BASE_DIR, "restaurant.json")
HOTEL_JSON = os.path.join(BASE_DIR, "hotel.json")
RESULT_JSON = os.path.join(BASE_DIR, "result.json")   # Used for filter results only.
ATTRACTION_JSON = os.path.join(BASE_DIR, "attraction.json")
LOCATION_JSON = os.path.join(BASE_DIR, "location.json")  # Used for merged recommendation data.

# 1. Serve the InteractiveMap.html page and inject the API key
@app.route('/')
def serve_html():
    api_key = os.getenv("AZURE_MAP_API")
    return render_template('InteractiveMap.html', api_key=api_key)

# Helper: wait for a file to exist with a timeout.
def wait_for_file(filepath, timeout=5):
    start_time = time.time()
    while not os.path.exists(filepath):
        if time.time() - start_time > timeout:
            return False
        time.sleep(0.5)
    return True

@app.route('/search_location', methods=['POST'])
def search_location():
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')
    if lat is None or lon is None:
        return jsonify({"error": "Missing latitude or longitude"}), 400

    results = {}
    for amenity, outfile in [('restaurant', RESTAURANT_JSON), ('hotel', HOTEL_JSON)]:
        if os.path.exists(RESULT_JSON):
            os.remove(RESULT_JSON)
        cmd = [sys.executable, FETCHING_DATA_SCRIPT, str(lat), str(lon), amenity]
        print(f"Executing: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"Error fetching {amenity}: {e.stderr}"}), 500

        if not wait_for_file(RESULT_JSON):
            return jsonify({"error": f"{RESULT_JSON} not found after fetching {amenity}"}), 500

        try:
            os.replace(RESULT_JSON, outfile)
        except Exception as ex:
            return jsonify({"error": f"Failed to replace {RESULT_JSON} to {outfile}: {str(ex)}"}), 500

        try:
            with open(outfile, "r", encoding="utf-8") as f:
                results[amenity] = json.load(f)
        except Exception as ex:
            return jsonify({"error": f"Error reading {outfile}: {str(ex)}"}), 500

    return jsonify({"message": "Location search completed", "results": results})

@app.route('/fetching_data', methods=['POST'])
def run_fetching_data():
    data = request.json
    lat = data.get('latitude')
    lon = data.get('longitude')
    amenity = data.get('amenity', 'restaurant')
    if lat is None or lon is None:
        return jsonify({"error": "Missing lat/lon"}), 400

    print(f"Received /fetching_data: lat={lat}, lon={lon}, amenity={amenity}")
    if not os.path.exists(FETCHING_DATA_SCRIPT):
        return jsonify({"error": f"{FETCHING_DATA_SCRIPT} not found"}), 500

    cmd = [sys.executable, FETCHING_DATA_SCRIPT, str(lat), str(lon), amenity]
    print("Executing:", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("fetching_data.py stdout:\n", result.stdout)
        if result.stderr:
            print("fetching_data.py stderr:\n", result.stderr)
    except subprocess.CalledProcessError as e:
        print("Error during subprocess call:", e.stderr)
        return jsonify({"error": f"fetching_data failed: {e.stderr}"}), 500
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500

    if not wait_for_file(RESULT_JSON):
        return jsonify({"error": "result.json not found after running fetching_data"}), 500

    try:
        with open(RESULT_JSON, "r", encoding="utf-8") as f:
            recommendations = json.load(f)
        if not isinstance(recommendations, list):
            return jsonify({"error": "Invalid format in result.json"}), 500
        return jsonify(recommendations)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in result.json"}), 500

@app.route('/restaurant_data', methods=['GET'])
def restaurant_data():
    try:
        with open(RESTAURANT_JSON, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"error": "restaurant.json not found"}), 404

@app.route('/hotel_data', methods=['GET'])
def hotel_data():
    try:
        with open(HOTEL_JSON, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"error": "hotel.json not found"}), 404

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')
    query = data.get('query', '').strip()
    if lat is None or lon is None or not query:
        return jsonify({"error": "Missing latitude, longitude, or query"}), 400

    if os.path.exists(RESULT_JSON):
        os.remove(RESULT_JSON)

    cmd = [sys.executable, FETCHING_DATA_SCRIPT, str(lat), str(lon), query]
    print(f"Executing recommendations: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Error fetching recommendations: {e.stderr}"}), 500

    if not wait_for_file(RESULT_JSON):
        return jsonify({"error": "result.json not found after fetching recommendations"}), 500

    try:
        with open(RESULT_JSON, "r", encoding="utf-8") as f:
            recommendations = json.load(f)
        return jsonify({"message": "Recommendations fetched", "recommendations": recommendations})
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in result.json"}), 500

@app.route('/attraction_data', methods=['POST'])
def attraction_data():
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')
    if lat is None or lon is None:
        return jsonify({"error": "Missing latitude or longitude"}), 400

    if os.path.exists(RESULT_JSON):
        os.remove(RESULT_JSON)

    cmd = [sys.executable, FETCHING_DATA_SCRIPT, str(lat), str(lon), "tourist attraction"]
    print(f"Executing attractions: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Error fetching attractions: {e.stderr}"}), 500

    if not wait_for_file(RESULT_JSON):
        return jsonify({"error": "result.json not found after fetching attractions"}), 500

    try:
        os.replace(RESULT_JSON, ATTRACTION_JSON)
    except Exception as ex:
        return jsonify({"error": f"Failed to replace result.json to {ATTRACTION_JSON}: {str(ex)}"}), 500

    try:
        with open(ATTRACTION_JSON, "r", encoding="utf-8") as f:
            attractions = json.load(f)
        return jsonify({"message": "Attractions fetched", "recommendations": attractions})
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in attraction.json"}), 500

# 8. Save filter results to result.json.
@app.route('/save_result', methods=['POST'])
def save_result():
    data = request.get_json()
    results = data.get("results", [])
    try:
        with open(RESULT_JSON, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        return jsonify({"message": "result.json saved", "results_count": len(results)})
    except Exception as ex:
        return jsonify({"error": f"Error saving result.json: {str(ex)}"}), 500

# 9. New endpoint to save merged recommendation data into a separate file (location.json).
@app.route('/save_location', methods=['POST'])
def save_location():
    data = request.get_json()
    results = data.get("results", [])
    try:
        with open(LOCATION_JSON, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        return jsonify({"message": "location.json saved", "results_count": len(results)})
    except Exception as ex:
        return jsonify({"error": f"Error saving location.json: {str(ex)}"}), 500

# 10. UPDATED: /upload_cosmos now directly queries Cosmos DB using address, filters,
# and a limit. Note that the filter clause now checks against c.description.
@app.route('/upload_cosmos', methods=['POST'])
def upload_cosmos():
    data = request.get_json() or {}
    address = data.get("address", "")
    filters = data.get("filters", [])
    limit = data.get("limit", 7)

    # Build the filter clause if filters are provided, using c.description.
    filters_clause = ""
    if filters:
        filters_clause = " OR ".join([f"CONTAINS(c.description, '{flt}')" for flt in filters])

    # Construct the query.
    query = f"SELECT TOP {limit} * FROM c WHERE c.address = '{address}' AND (c.type IN ('hotel','restaurant','attraction')"
    if filters_clause:
        query += f" OR {filters_clause}"
    query += ")"

    try:
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        return jsonify({"places": items, "query": query})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 11. New endpoint to process the location file with Azure OpenAI.
@app.route('/process_locations', methods=['POST'])
def process_locations():
    try:
        location_data = request.get_json()
        if not location_data:
            return jsonify({"error": "No location data provided"}), 400

        from openai import AzureOpenAI

        client_ai = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-03-01-preview"
        )

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant designed to output JSON. Please analyze the provided location data and return a valid JSON object."
            },
            {
                "role": "user",
                "content": json.dumps(location_data)
            }
        ]

        response = client_ai.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=messages
        )
        output = response.choices[0].message.content
        return jsonify({"message": "Processing complete", "result": output})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

# 12. New endpoint to save user input (address and filter) into Cosmos DB.
@app.route('/save_user_input', methods=['POST'])
def save_user_input():
    data = request.get_json()
    user_address = data.get('user_address')
    user_filter = data.get('user_filter')
    if not user_address:
        return jsonify({"error": "User address is required."}), 400

    document = {
        'id': str(uuid.uuid4()),
        'user_address': user_address,
        'user_filter': user_filter,
        'type': 'user_input'
    }

    try:
        container.create_item(document)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "User input saved successfully."})

# 13. Start the Flask server with the correct host & port.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
