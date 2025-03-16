import sys
import os
from dotenv import load_dotenv
import serpapi
import requests
import json

# Ensure correct number of arguments
if len(sys.argv) != 3:
    print('Usage: python demoMix.py <latitude> <longitude>')
    sys.exit(1)

# Retrieve coordinates from command-line arguments
user_lat = float(sys.argv[1])
user_lon = float(sys.argv[2])

print(f"Received coordinates: {user_lat}, {user_lon}")

# Load environment variables
load_dotenv()

# Load the SerpAPI key for Google Maps queries
serp_api_key = os.getenv('SERPAPI_KEY')
client = serpapi.Client(api_key=serp_api_key)

# Azure Maps Subscription Key
SUBSCRIPTION_KEY = '9FeaTsMg7fH5DgcchS5AtICBBNTWnuoBHNG4H0a3OLzkxTeY9lHnJQQJ99BCACYeBjF6fAFpAAAgAZMP2bXk'

def generate_ll_param(lat, lon, zoom=20):
    """
    Formats latitude and longitude into the format expected by the SerpAPI parameter.
    Example: '@40.712776,-74.005974,20z'
    """
    return f"@{lat},{lon},{zoom}z"

def main():
    try:
        # Define amenity - default to "restaurant"
        amenity = "restaurant"

        # Use the coordinates from command-line arguments
        latitude = user_lat
        longitude = user_lon

        # Format the latitude/longitude for the API request
        ll_param = generate_ll_param(latitude, longitude)
        print(f"Searching for {amenity} near: {latitude}, {longitude}")

        # Use SerpAPI to perform a Google Maps search with the dynamic parameters
        params = {
            'engine': 'google_maps',
            'q': amenity,
            'type': 'search',
            'll': ll_param,
        }
        results = client.search(params)

        # Extract locations from the results
        if "places_results" in results:
            locations = results["places_results"][:5]
        elif "local_results" in results:
            locations = results["local_results"][:5]
        elif "results" in results:
            locations = results["results"][:5]
        else:
            locations = []

        # Process locations into a structured JSON format
        reduced_locations = []
        for loc in locations:
            # Extract coordinates from "gps_coordinates"
            gps = loc.get("gps_coordinates")
            if gps:
                lat = gps.get("latitude")
                lon = gps.get("longitude")
            else:
                # Fallback: check if coordinates exist under geometry -> location
                geo = loc.get("geometry", {}).get("location", {})
                lat = geo.get("lat")
                lon = geo.get("lng")

            reduced_locations.append({
                "Name": loc.get("title"),
                "Address": loc.get("address"),
                "Rating": loc.get("rating"),
                "Price": loc.get("price"),
                "Opening Hour": loc.get("hours", loc.get("open_state")),
                "Latitude": lat,
                "Longitude": lon
            })

        # Write the results to a JSON file
        output_filename = "result.json"
        with open(output_filename, "w", encoding="utf-8") as json_file:
            json.dump(reduced_locations, json_file, indent=4)

        print(f"[INFO] Search results have been saved to {output_filename}")

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
