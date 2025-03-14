import requests
import pandas as pd
from datetime import datetime

# Replace with your actual Azure Maps subscription key
SUBSCRIPTION_KEY = '9FeaTsMg7fH5DgcchS5AtICBBNTWnuoBHNG4H0a3OLzkxTeY9lHnJQQJ99BCACYeBjF6fAFpAAAgAZMP2bXk'

def get_coordinates(destination):
    address_url = "https://atlas.microsoft.com/search/address/json"
    params = {
        "subscription-key": SUBSCRIPTION_KEY,
        "api-version": "1.0",
        "query": destination
    }
    response = requests.get(address_url, params=params)
    print("Geocoding response:", response.text)  # Debug print
    if response.status_code == 200:
        data = response.json()
        if data.get("results"):
            position = data["results"][0]["position"]
            return position["lat"], position["lon"]
        else:
            raise Exception("No matching address found.")
    else:
        raise Exception(f"Address API error: {response.status_code}")

def search_pois(lat, lon, query_filter):
    poi_url = "https://atlas.microsoft.com/search/poi/json"
    params = {
        "subscription-key": SUBSCRIPTION_KEY,
        "api-version": "1.0",
        "lat": lat,
        "lon": lon,
        "query": query_filter,
        "limit": 20  # get more in case some entries lack additional details
    }
    response = requests.get(poi_url, params=params)
    print("POI search response:", response.text)  # Debug print
    if response.status_code == 200:
        data = response.json()
        pois = []
        for item in data.get("results", []):
            poi = {
                "name": item.get("poi", {}).get("name", ""),
                "address": item.get("address", {}).get("freeformAddress", ""),
                "category": item.get("poi", {}).get("categories", [""])[0],
                "lat": item.get("position", {}).get("lat", None),
                "lon": item.get("position", {}).get("lon", None)
            }
            pois.append(poi)
        # Limit to the first 10 entries
        return pois[:10]
    else:
        raise Exception(f"POI API error: {response.status_code}")

def get_route_distance(origin_lat, origin_lon, dest_lat, dest_lon):
    route_url = "https://atlas.microsoft.com/route/directions/json"
    params = {
        "subscription-key": SUBSCRIPTION_KEY,
        "api-version": "1.0",
        "query": f"{origin_lat},{origin_lon}:{dest_lat},{dest_lon}",
        "travelMode": "driving"
    }
    response = requests.get(route_url, params=params)
    print("Route response:", response.text)  # Debug print
    if response.status_code == 200:
        data = response.json()
        if data.get("routes"):
            # Extract the distance (meters) from the summary
            distance = data["routes"][0]["summary"]["lengthInMeters"]
            return distance
        else:
            print("Route response did not contain routes:", data)
            raise Exception("No route found.")
    else:
        raise Exception(f"Route API error: {response.status_code}")

def main():
    destination = input("Enter destination: ")
    poi_filter = input("Enter POI filter (e.g. restaurant, cafe, hotel, etc.) [default: restaurant]: ")
    if not poi_filter:
        poi_filter = "restaurant"
    try:
        # Get user's coordinate for the destination
        origin_lat, origin_lon = get_coordinates(destination)
        print(f"Coordinates for '{destination}': {origin_lat}, {origin_lon}")
        
        pois = search_pois(origin_lat, origin_lon, poi_filter)
        if not pois:
            print("No POIs found for the selected filter.")
            return
        
        # For each found POI, compute the driving distance from the user-specified destination.
        for poi in pois:
            if poi["lat"] is not None and poi["lon"] is not None:
                try:
                    distance = get_route_distance(origin_lat, origin_lon, poi["lat"], poi["lon"])
                    poi["distance_meters"] = distance
                except Exception as e:
                    print(f"Error fetching route for {poi['name']}: {e}")
                    poi["distance_meters"] = None
            else:
                poi["distance_meters"] = None
        
        # Export the results to CSV
        df = pd.DataFrame(pois)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f'pois_{timestamp}.csv'
        df.to_csv(csv_filename, index=False)
        print(f"Extracted data for {len(pois)} POIs has been exported to {csv_filename}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()