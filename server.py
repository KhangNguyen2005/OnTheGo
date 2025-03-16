from flask import Flask, request, jsonify, send_from_directory
import json
import subprocess
import os
import time

app = Flask(__name__)

DEMOMIX_SCRIPT = "demoMix.py"
RESULT_JSON = "result.json"

@app.route('/')
def serve_html():
    # Serve your Test.html
    return send_from_directory('.', 'Test.html')

@app.route('/demoMix', methods=['POST'])
def run_demoMix():
    """Receives lat, lon, amenity from the frontend, runs demoMix.py, returns recommendations."""
    data = request.json
    lat = data.get('latitude')
    lon = data.get('longitude')
    amenity = data.get('amenity', 'restaurant')

    if lat is None or lon is None:
        return jsonify({"error": "Missing lat/lon"}), 400

    print(f"Received /demoMix: lat={lat}, lon={lon}, amenity={amenity}")

    if not os.path.exists(DEMOMIX_SCRIPT):
        return jsonify({"error": f"{DEMOMIX_SCRIPT} not found"}), 500

    # Build the command to call demoMix.py
    cmd = ["python", DEMOMIX_SCRIPT, str(lat), str(lon), amenity]
    print("Executing:", " ".join(cmd))

    try:
        # Run the command & capture output
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("demoMix.py stdout:\n", result.stdout)
        if result.stderr:
            print("demoMix.py stderr:\n", result.stderr)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"demoMix failed: {e.stderr}"}), 500
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500

    # Wait up to 5 seconds for result.json
    start_time = time.time()
    timeout = 5
    while not os.path.exists(RESULT_JSON):
        if (time.time() - start_time) > timeout:
            return jsonify({"error": "result.json not found after running demoMix"}), 500
        time.sleep(0.5)

    # Load the JSON data from result.json
    try:
        with open(RESULT_JSON, "r", encoding="utf-8") as f:
            recommendations = json.load(f)

        # Must be a list for the front-end to handle
        if not isinstance(recommendations, list):
            return jsonify({"error": "Invalid format in result.json"}), 500

        return jsonify(recommendations)

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in result.json"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
