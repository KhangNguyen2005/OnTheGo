import requests
import pandas as pd
from datetime import datetime

# Replace with your actual Google API key
GOOGLE_API_KEY = ''

def get_coordinates(destination):
    """
    Get the latitude and longitude of the destination using the Google Geocoding API.
    """
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": destination,
        "key": GOOGLE_API_KEY
    }
    response = requests.get(geocode_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
        else:
            raise Exception("Geocoding API error: " + data["status"])
    else:
        raise Exception("HTTP error with Geocoding API: " + str(response.status_code))

def search_places(lat, lon, query_filter, radius=5000):
    """
    Search for points of interest using the Google Places API.
    Extracts the name, address, rating, and total number of ratings.
    """
    places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lon}",
        "radius": radius,
        "keyword": query_filter,
        "key": GOOGLE_API_KEY
    }
    response = requests.get(places_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "OK":
            places = []
            for place in data.get("results", []):
                place_info = {
                    "name": place.get("name", ""),
                    "address": place.get("vicinity", ""),
                    "rating": place.get("rating", None),
                    "user_ratings_total": place.get("user_ratings_total", None)
                }
                places.append(place_info)
            return places
        else:
            raise Exception("Places API error: " + data["status"])
    else:
        raise Exception("HTTP error with Places API: " + str(response.status_code))

def main():
    destination = input("Enter destination: ")
    query_filter = input("Enter POI filter (e.g. restaurant, cafe, hotel) [default: restaurant]: ")
    if not query_filter:
        query_filter = "restaurant"
    try:
        lat, lon = get_coordinates(destination)
        print(f"Coordinates for '{destination}': {lat}, {lon}")
        places = search_places(lat, lon, query_filter)
        if not places:
            print("No places found for the selected filter.")
            return
        df = pd.DataFrame(places)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"google_places_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"Extracted data for {len(places)} places has been exported to {csv_filename}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()