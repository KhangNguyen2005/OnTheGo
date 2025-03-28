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
    raise Exception("COSMOS_ENDPOINT and COSMOS_DB_KEY must be set in environment variables.")

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

# 9. New endpoint to save merged recommendation data into a separate file (location.json)
# and then immediately upload each document to Cosmos DB.
@app.route('/save_location', methods=['POST'])
def save_location():
    try:
        merged = []
        # Merge data from restaurant.json, hotel.json, and attraction.json if they exist.
        for file_path in [RESTAURANT_JSON, HOTEL_JSON, ATTRACTION_JSON]:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        if isinstance(data, list):
                            merged.extend(data)
                        else:
                            merged.append(data)
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] Error decoding JSON from {file_path}: {e}")

        # Save the merged recommendations to location.json.
        with open(LOCATION_JSON, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=4)

        # Upload the merged recommendations to Cosmos DB.
        for doc in merged:
            # If amenity_type is missing, try to extract it from Description.
            if "amenity_type" not in doc:
                if "Description" in doc:
                    parts = doc["Description"].split(',')
                    if parts:
                        doc["amenity_type"] = parts[-1].strip().lower()
                    else:
                        doc["amenity_type"] = "unknown"
                else:
                    doc["amenity_type"] = "unknown"

            # Generate an id from amenity_type and Name (or name) if possible.
            if "id" not in doc:
                if "Name" in doc or "name" in doc:
                    name_field = doc.get("Name") or doc.get("name") or ""
                    doc["id"] = (doc["amenity_type"] + "_" + name_field).replace(" ", "_")
                else:
                    doc["id"] = str(uuid.uuid4())
            if "ItemID" not in doc:
                doc["ItemID"] = doc["id"]

            container.upsert_item(doc)

        return jsonify({
            "message": "location.json saved and data uploaded to Cosmos DB",
            "results_count": len(merged)
        })
    except Exception as ex:
        return jsonify({"error": f"Error saving location.json: {str(ex)}"}), 500

# 10. New endpoint to process the location file with Azure OpenAI.
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

# 11. New endpoint to save user input (address and filter) into Cosmos DB.
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

@app.route('/generate_plan', methods=['POST'])
def generate_plan():
    try:
        # Step 1: Push the latest recommendations to Cosmos DB.
        UPLOAD_COSMOS_SCRIPT = os.path.join(BASE_DIR, "upload_cosmos.py")
        subprocess.run(
            [sys.executable, UPLOAD_COSMOS_SCRIPT],
            capture_output=True,
            text=True,
            check=True
        )
        print("[INFO] upload_cosmos.py executed successfully.")

        # Step 2: Run query_top_places.py to generate top_places_by_amenity.json.
        QUERY_TOP_PLACES_SCRIPT = os.path.join(BASE_DIR, "query_top_places.py")
        subprocess.run(
            [sys.executable, QUERY_TOP_PLACES_SCRIPT],
            capture_output=True,
            text=True,
            check=True
        )
        print("[INFO] query_top_places.py executed successfully.")

        # Step 3: Run ai_integration.py to generate the travel plan.
        AI_INTEGRATION_SCRIPT = os.path.join(BASE_DIR, "ai_integration.py")
        subprocess.run(
            [sys.executable, AI_INTEGRATION_SCRIPT],
            capture_output=True,
            text=True,
            check=True
        )
        print("[INFO] ai_integration.py executed successfully.")

        # Step 4: Read plan.json from disk.
        plan_file = os.path.join(BASE_DIR, "plan.json")
        if not os.path.exists(plan_file):
            return jsonify({"error": "plan.json not found."}), 500

        with open(plan_file, "r", encoding="utf-8") as f:
            plan_data = json.load(f)

        # If plan_data is a string (i.e. double-encoded), parse it again.
        if isinstance(plan_data, str):
            plan_data = json.loads(plan_data)

        # Extract all "Location" values from the travel plan.
        locations = []
        if isinstance(plan_data, dict) and "travel_plan" in plan_data:
            for period, activities in plan_data["travel_plan"].items():
                for activity in activities:
                    # Ensure activity is a dictionary; if it's a string, try to parse it.
                    if isinstance(activity, dict):
                        location = activity.get("Location")
                        if location:
                            locations.append(location)
                    elif isinstance(activity, str):
                        try:
                            activity_obj = json.loads(activity)
                        except Exception:
                            activity_obj = {}
                        location = activity_obj.get("Location")
                        if location:
                            locations.append(location)

        if not locations:
            return jsonify({
                "error": "No locations found in plan.json.",
                "plan_data": plan_data
            }), 500

        # Return both 'locations' and the entire 'travel_plan'
        return jsonify({
            "message": "Plan generated successfully",
            "locations": locations,
            "travel_plan": plan_data.get("travel_plan", {})
        })
    except subprocess.CalledProcessError as e:
        print("Subprocess error:", e.stderr)
        return jsonify({"error": f"Subprocess error: {e.stderr}"}), 500
    except Exception as ex:
        print("General error:", str(ex))
        return jsonify({"error": str(ex)}), 500

# Start the Flask server with the correct host & port.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
