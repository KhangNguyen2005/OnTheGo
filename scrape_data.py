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
    if response.status_code == 200:
        data = response.json()
        pois = []
        for item in data.get("results", []):
            poi = {
                "name": item.get("poi", {}).get("name", ""),
                "address": item.get("address", {}).get("freeformAddress", ""),
                "category": item.get("poi", {}).get("categories", [""])[0],
                # "rating": item.get("rating", None)  # Note: Azure Maps may not provide rating info.
            }
            pois.append(poi)
        # Limit to the first 10 entries
        return pois[:10]
    else:
        raise Exception(f"POI API error: {response.status_code}")

def main():
    destination = input("Enter destination: ")
    poi_filter = input("Enter POI filter (e.g. restaurant, cafe, hotel, etc.) [default: restaurant]: ")
    if not poi_filter:
        poi_filter = "restaurant"
    try:
        lat, lon = get_coordinates(destination)
        print(f"Coordinates for '{destination}': {lat}, {lon}")
        
        pois = search_pois(lat, lon, poi_filter)
        if not pois:
            print("No POIs found for the selected filter.")
            return
        
        df = pd.DataFrame(pois)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f'pois_{timestamp}.csv'
        df.to_csv(csv_filename, index=False)
        print(f"Extracted data for {len(pois)} POIs has been exported to {csv_filename}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()