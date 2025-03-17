from flask import Flask, request, jsonify, send_from_directory
import json
import subprocess
import os
import time

app = Flask(__name__)

FETCHING_DATA_SCRIPT = "fetching_data.py"
RESULT_JSON = "result.json"

@app.route('/')
def serve_html():
    # Serve your Test.html
    return send_from_directory('.', 'InteractiveMap.html')

@app.route('/fetching_data', methods=['POST'])
def run_fetching_data():
    """Receives latitude, longitude, and amenity from the frontend,
    runs fetching_data.py, and returns recommendations."""
    data = request.json
    lat = data.get('latitude')
    lon = data.get('longitude')
    amenity = data.get('amenity', 'restaurant')

    if lat is None or lon is None:
        return jsonify({"error": "Missing lat/lon"}), 400

    print(f"Received /fetching_data: lat={lat}, lon={lon}, amenity={amenity}")

    if not os.path.exists(FETCHING_DATA_SCRIPT):
        return jsonify({"error": f"{FETCHING_DATA_SCRIPT} not found"}), 500

    # Build the command to call fetching_data.py
    cmd = ["python", FETCHING_DATA_SCRIPT, str(lat), str(lon), amenity]
    print("Executing:", " ".join(cmd))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("fetching_data.py stdout:\n", result.stdout)
        if result.stderr:
            print("fetching_data.py stderr:\n", result.stderr)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"fetching_data failed: {e.stderr}"}), 500
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500

    # Wait up to 5 seconds for result.json to appear
    start_time = time.time()
    timeout = 5
    while not os.path.exists(RESULT_JSON):
        if (time.time() - start_time) > timeout:
            return jsonify({"error": "result.json not found after running fetching_data"}), 500
        time.sleep(0.5)

    try:
        with open(RESULT_JSON, "r", encoding="utf-8") as f:
            recommendations = json.load(f)
        if not isinstance(recommendations, list):
            return jsonify({"error": "Invalid format in result.json"}), 500

        return jsonify(recommendations)

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in result.json"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
