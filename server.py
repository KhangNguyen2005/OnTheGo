from flask import Flask, request, jsonify, send_from_directory
import json
import subprocess
import os
import time
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = os.environ.get("MY_APP_BASE_DIR", os.path.abspath(os.path.dirname(__file__)))
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)

# File and script names using absolute paths.
FETCHING_DATA_SCRIPT = os.path.join(BASE_DIR, "fetching_data.py")
RESTAURANT_JSON = os.path.join(BASE_DIR, "restaurant.json")
HOTEL_JSON = os.path.join(BASE_DIR, "hotel.json")
RESULT_JSON = os.path.join(BASE_DIR, "result.json")   # Used for filter results only.
ATTRACTION_JSON = os.path.join(BASE_DIR, "attraction.json")
LOCATION_JSON = os.path.join(BASE_DIR, "location.json")  # Used for merged recommendation data.

# 1. Serve the InteractiveMap.html page.
@app.route('/')
def serve_html():
    return send_from_directory(BASE_DIR, 'InteractiveMap.html')

# Helper: wait for a file to exist with a timeout.
def wait_for_file(filepath, timeout=5):
    start_time = time.time()
    while not os.path.exists(filepath):
        if time.time() - start_time > timeout:
            return False
        time.sleep(0.5)
    return True

# 2. Automatically fetch restaurants & hotels when a location is selected.
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
            os.rename(RESULT_JSON, outfile)
        except Exception as ex:
            return jsonify({"error": f"Failed to rename {RESULT_JSON} to {outfile}: {str(ex)}"}), 500

        try:
            with open(outfile, "r", encoding="utf-8") as f:
                results[amenity] = json.load(f)
        except Exception as ex:
            return jsonify({"error": f"Error reading {outfile}: {str(ex)}"}), 500

    return jsonify({"message": "Location search completed", "results": results})

# 3. Fetching data dynamically for custom queries.
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

# 4. Serve restaurant data.
@app.route('/restaurant_data', methods=['GET'])
def restaurant_data():
    try:
        with open(RESTAURANT_JSON, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"error": "restaurant.json not found"}), 404

# 5. Serve hotel data.
@app.route('/hotel_data', methods=['GET'])
def hotel_data():
    try:
        with open(HOTEL_JSON, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"error": "hotel.json not found"}), 404

# 6. Handle user search queries & save recommendations in result.json.
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

# 7. New endpoint for Attractions (Recommendations).
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
        os.rename(RESULT_JSON, ATTRACTION_JSON)
    except Exception as ex:
        return jsonify({"error": f"Failed to rename result.json to {ATTRACTION_JSON}: {str(ex)}"}), 500

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

# 10. New endpoint to process the location file with Azure OpenAI.
@app.route('/process_locations', methods=['POST'])
def process_locations():
    try:
        # Get the location data from the client
        location_data = request.get_json()
        if not location_data:
            return jsonify({"error": "No location data provided"}), 400

        # Import AzureOpenAI from openai package.
        from openai import AzureOpenAI

        # Instantiate the AzureOpenAI client with endpoint, api_key, and api_version.
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-03-01-preview"
        )

        # Prepare messages with a system instruction and the location data as user content.
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

        # Send the chat request with response_format set to JSON mode.
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=messages
        )

        # Get the output from the model.
        output = response.choices[0].message.content
        return jsonify({"message": "Processing complete", "result": output})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

# 11. Start the Flask server with the correct host & port.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
