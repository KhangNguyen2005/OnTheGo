from flask import Flask, request, jsonify, send_from_directory
import json
import subprocess
import os
import time

app = Flask(__name__)

# Paths
DEMOMIX_PATH = "E:\\Workspace\\OnTheGo\\demoMix.py"  # Path to the demoMix script
RESULT_JSON_PATH = "E:\\Workspace\\OnTheGo\\result.json"  # Path to the result.json file

@app.route('/')
def serve_map():
    return send_from_directory('.', 'Test.html')

@app.route('/demoMix', methods=['POST'])
def run_demoMix():
    """Handles coordinate input, logs coordinates, runs demoMix, and returns recommendations."""
    data = request.json
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if latitude is None or longitude is None:
        return jsonify({"error": "Missing coordinates"}), 400

    print(f"Received coordinates: Latitude={latitude}, Longitude={longitude}")

    try:
        # Check if demoMix.py exists
        if not os.path.exists(DEMOMIX_PATH):
            print("Error: demoMix.py not found")
            return jsonify({"error": "demoMix.py not found"}), 500

        # Construct command to run demoMix.py
        command = ["python", DEMOMIX_PATH, str(latitude), str(longitude)]
        print(f"Executing: {' '.join(command)}")

        # Run demoMix.py and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("demoMix Output:", result.stdout)

    except subprocess.CalledProcessError as e:
        print("demoMix Error:", e.stderr)
        return jsonify({"error": f"demoMix execution failed: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Wait for result.json to be generated
    timeout = 5
    start_time = time.time()
    while not os.path.exists(RESULT_JSON_PATH):
        if time.time() - start_time > timeout:
            print("Error: result.json not found after running demoMix.py")
            return jsonify({"error": "result.json not found after running demoMix"}), 500
        time.sleep(0.5)

    # Load result.json and return recommendations
    try:
        with open(RESULT_JSON_PATH, "r", encoding="utf-8") as file:
            recommendations = json.load(file)

        if not isinstance(recommendations, list):  # Ensure the structure is correct
            print("Error: result.json does not contain a valid list")
            return jsonify({"error": "Invalid data format in result.json"}), 500

        return jsonify(recommendations)

    except json.JSONDecodeError:
        print("Error: result.json contains invalid JSON")
        return jsonify({"error": "Invalid JSON format in result.json"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
