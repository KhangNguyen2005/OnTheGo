import sys
import os
import math
import json
import traceback
from dotenv import load_dotenv
import serpapi

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

if len(sys.argv) < 3:
    print('Usage: python fetching_data.py <latitude> <longitude> [search query]')
    sys.exit(1)

try:
    latitude = float(sys.argv[1])
    longitude = float(sys.argv[2])
except ValueError as ve:
    print("[ERROR] Invalid latitude or longitude:", ve)
    sys.exit(1)

# Join all additional arguments into one query string to support both address and description.
query = " ".join(sys.argv[3:]) if len(sys.argv) >= 4 else "restaurant"

serp_api_key = os.getenv('SERPAPI_KEY')
if not serp_api_key:
    print("Error: SERPAPI_KEY not found in environment variables.")
    sys.exit(1)

client = serpapi.Client(api_key=serp_api_key)

def generate_ll_param(lat, lon, zoom=16):
    return f"@{lat},{lon},{zoom}z"

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)."""
    R = 6371  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def main():
    try:
        ll_param = generate_ll_param(latitude, longitude)
        params = {
            'engine': 'google_maps',
            'q': query,
            'type': 'search',
            'll': ll_param
        }

        results = client.search(params)
        # Try to get the list of locations from one of the possible keys
        locations = results.get("places_results") or results.get("local_results") or results.get("results") or []
        
        # Filter locations to only include those within 20km
        filtered_locations = []
        for loc in locations:
            gps = loc.get("gps_coordinates", {})
            lat_val = gps.get("latitude")
            lon_val = gps.get("longitude")
            if lat_val is None or lon_val is None:
                geo = loc.get("geometry", {}).get("location", {})
                lat_val = geo.get("lat")
                lon_val = geo.get("lng")
            # If we still don't have coordinates, skip the result
            if lat_val is None or lon_val is None:
                continue

            distance = haversine(latitude, longitude, lat_val, lon_val)
            if distance <= 20:
                filtered_locations.append({
                    "Name": loc.get("title"),
                    "Address": loc.get("address"),
                    "Rating": loc.get("rating"),
                    "Price": loc.get("price"),
                    "Opening Hour": loc.get("hours", loc.get("open_state")),
                    # NEW: Build Description as "address, type of amenity"
                    "Description": (loc.get("address", "") + ", " + loc.get("type", "")).strip(),
                    "Latitude": lat_val,
                    "Longitude": lon_val,
                    "Distance (km)": round(distance, 2)
                })

        # Limit to 10 results if necessary
        output_data = filtered_locations[:10]

        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4)

        print(f"[INFO] result.json saved with {len(output_data)} results within 20km radius.")
    except Exception as e:
        print(f"[ERROR] {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
