import sys
import os
from dotenv import load_dotenv
import serpapi
import json

"""
Usage: python demoMix.py <latitude> <longitude> [amenity]
 - <latitude>, <longitude>: float
 - [amenity]: optional, defaults to "restaurant"
"""

if len(sys.argv) < 3:
    print('Usage: python demoMix.py <latitude> <longitude> [amenity]')
    sys.exit(1)

latitude = float(sys.argv[1])
longitude = float(sys.argv[2])
amenity = sys.argv[3] if len(sys.argv) >= 4 else "restaurant"

# Load environment variables from .env (SERPAPI_KEY)
load_dotenv()

serp_api_key = os.getenv('SERPAPI_KEY')  # e.g. "e183cd43fd..."
if not serp_api_key:
    print("Error: SERPAPI_KEY not found in environment variables.")
    sys.exit(1)

print(f"Received coordinates: {latitude}, {longitude}")
print(f"Searching for amenity: {amenity}")

# Create SerpAPI client
client = serpapi.Client(api_key=serp_api_key)

def generate_ll_param(lat, lon, zoom=16):
    """
    Formats lat/lon for the SerpAPI request (google_maps engine).
    Example: '@40.712776,-74.005974,16z'
    """
    return f"@{lat},{lon},{zoom}z"

def main():
    try:
        ll_param = generate_ll_param(latitude, longitude)
        # Prepare params for the Google Maps search
        params = {
            'engine': 'google_maps',
            'q': amenity,
            'type': 'search',
            'll': ll_param
        }

        # Run the search
        results = client.search(params)

        # Extract up to 5 places
        if "places_results" in results:
            locations = results["places_results"][:5]
        elif "local_results" in results:
            locations = results["local_results"][:5]
        elif "results" in results:
            locations = results["results"][:5]
        else:
            locations = []

        # Build a JSON structure for each place
        output_data = []
        for loc in locations:
            gps = loc.get("gps_coordinates") or {}
            lat = gps.get("latitude")
            lon = gps.get("longitude")

            # Fallback if gps_coordinates is missing
            if lat is None or lon is None:
                geo = loc.get("geometry", {}).get("location", {})
                lat = geo.get("lat")
                lon = geo.get("lng")

            output_data.append({
                "Name": loc.get("title"),
                "Address": loc.get("address"),
                "Rating": loc.get("rating"),
                "Price": loc.get("price"),
                "Opening Hour": loc.get("hours", loc.get("open_state")),
                "Latitude": lat,
                "Longitude": lon
            })

        # Write the data to result.json
        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4)

        print(f"[INFO] result.json saved with {len(output_data)} results.")

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
