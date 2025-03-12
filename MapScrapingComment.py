import requests
import pandas as pd
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
import requests
import pandas as pd
from datetime import datetime
import urllib.parse
import math



# Replace with your actual Azure Maps subscription key
SUBSCRIPTION_KEY = '9FeaTsMg7fH5DgcchS5AtICBBNTWnuoBHNG4H0a3OLzkxTeY9lHnJQQJ99BCACYeBjF6fAFpAAAgAZMP2bXk'

def get_coordinates(destination):
    """
    Converts an address into latitude and longitude using Azure Maps Geocoding API.
    """
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
    """
    Searches for POIs near given coordinates using Azure Maps.
    Returns a list of dictionaries containing name, address, category, and coordinates.
    """
    poi_url = "https://atlas.microsoft.com/search/poi/json"
    params = {
        "subscription-key": SUBSCRIPTION_KEY,
        "api-version": "1.0",
        "lat": lat,
        "lon": lon,
        "query": query_filter,
        "limit": 20  # get more in case some entries lack details
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
                "lat": item.get("position", {}).get("lat", None),
                "lon": item.get("position", {}).get("lon", None)
            }
            pois.append(poi)
        return pois[:10]  # limit to first 10 entries
    else:
        raise Exception(f"POI API error: {response.status_code}")

def generate_google_maps_link(poi_name, address):
    """
    Generates a Google Maps search URL using both the POI's name and address.
    """
    query = f"{poi_name} {address}"
    search_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query)}"
    return search_url

def validate_link(url):
    """
    Validates that the provided Google Maps link returns content that does not indicate a failed search.
    This is a heuristic check that looks for phrases indicating no results.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return False
        lower_text = response.text.lower()
        if "did not match any" in lower_text or "no results found" in lower_text:
            return False
        return True
    except Exception as e:
        print(f"Error validating URL {url}: {e}")
        return False

def haversine(lat1, lon1, lat2, lon2):
    """
    Compute the great-circle distance between two points on the Earth.
    Returns the distance in kilometers.
    """
    R = 6371  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def main():
    destination = input("Enter destination: ")
    poi_filter = input("Enter POI filter (e.g. restaurant, cafe, hotel, etc.) [default: restaurant]: ")
    if not poi_filter:
        poi_filter = "restaurant"
    try:
        # Get coordinates for the destination (used for sorting and deduplication)
        dest_lat, dest_lon = get_coordinates(destination)
        print(f"\nCoordinates for '{destination}': {dest_lat}, {dest_lon}\n")
        
        # Search for nearby POIs
        pois = search_pois(dest_lat, dest_lon, poi_filter)
        
        # Validate and filter POIs with valid Google Maps links using both name and address
        valid_pois = []
        for poi in pois:
            if poi["address"]:
                maps_link = generate_google_maps_link(poi["name"], poi["address"])
                if validate_link(maps_link):
                    poi["maps_link"] = maps_link
                    # Calculate distance from the destination to the POI (using lat/lon)
                    if poi["lat"] and poi["lon"]:
                        poi["distance_km"] = haversine(dest_lat, dest_lon, poi["lat"], poi["lon"])
                    else:
                        poi["distance_km"] = float('inf')
                    valid_pois.append(poi)
                else:
                    print(f"Link for '{poi['name']}' with address '{poi['address']}' is invalid and has been omitted.")
            else:
                print(f"Address not available for '{poi['name']}', skipping link generation.")
        
        if not valid_pois:
            print("No valid POIs with working Google Maps links were found.")
            return
        
        # Deduplicate: if addresses are the same, keep the one with the smallest distance
        unique_pois = {}
        for poi in valid_pois:
            addr = poi["address"].strip().lower()
            if addr not in unique_pois or poi.get("distance_km", float('inf')) < unique_pois[addr].get("distance_km", float('inf')):
                unique_pois[addr] = poi
        
        dedup_valid_pois = list(unique_pois.values())
        dedup_valid_pois.sort(key=lambda x: x.get("distance_km", float('inf')))
        
        # Print each valid deduplicated POI in the requested format:
        print("\nValid and deduplicated POIs to be included:")
        for idx, poi in enumerate(dedup_valid_pois, start=1):
            print(f"{idx}.")
            print(f"   Name: {poi['name']}")
            print(f"   Address: {poi['address']}")
            print(f"   Category: {poi['category']}")
            print(f" {poi['maps_link']}\n")
        
        # Prepare the output for CSV export (includes full details)
        output_pois = []
        for poi in dedup_valid_pois:
            output_poi = {
                "Type of amenity": poi["category"],
                "Name": poi["name"],
                "Address": poi["address"],
                "Google Maps Link": poi["maps_link"]
            }
            output_pois.append(output_poi)
        
        # Export the results to a CSV file with the specified column order
        df = pd.DataFrame(output_pois, columns=["Type of amenity", "Name", "Address", "Google Maps Link"])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f'pois_with_valid_links_{timestamp}.csv'
        df.to_csv(csv_filename, index=False)
        print(f"\nExtracted data for {len(output_pois)} valid POIs has been exported to {csv_filename}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()