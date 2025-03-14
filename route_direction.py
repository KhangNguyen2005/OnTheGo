import os
import json
import requests
import folium
import webbrowser

# Replace with your actual Azure Maps subscription key.
AZURE_MAPS_SUBSCRIPTION_KEY = '9FeaTsMg7fH5DgcchS5AtICBBNTWnuoBHNG4H0a3OLzkxTeY9lHnJQQJ99BCACYeBjF6fAFpAAAgAZMP2bXk'

def decode_polyline(polyline_str):
    """
    Decodes an encoded polyline string into a list of (latitude, longitude) tuples.
    Follows the Google polyline algorithm.
    """
    index, lat, lng = 0, 0, 0
    coordinates = []
    while index < len(polyline_str):
        shift, result = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        shift, result = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        coordinates.append((lat * 1e-5, lng * 1e-5))
    return coordinates

class AzureMapsGeocoder:
    def __init__(self):
        self.subscription_key = AZURE_MAPS_SUBSCRIPTION_KEY
        self.endpoint = "https://atlas.microsoft.com/search/address/json"
        self.api_version = "1.0"
    
    def get_coordinates(self, location):
        params = {
            "api-version": self.api_version,
            "query": location,
            "subscription-key": self.subscription_key
        }
        response = requests.get(self.endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                position = results[0].get("position", {})
                return position.get("lat"), position.get("lon")
            else:
                print("No results found for the location.")
        else:
            print("Error fetching geocode data:", response.status_code, response.text)
        return None, None

class AzureMapsPOISearch:
    def __init__(self):
        self.subscription_key = AZURE_MAPS_SUBSCRIPTION_KEY
        self.endpoint = "https://atlas.microsoft.com/search/poi/json"
        self.api_version = "1.0"
    
    def search_poi(self, lat, lon, category, radius=5000, limit=5):
        params = {
            "api-version": self.api_version,
            "query": category,
            "lat": lat,
            "lon": lon,
            "radius": radius,
            "limit": limit,
            "subscription-key": self.subscription_key
        }
        response = requests.get(self.endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            poi_list = []
            for result in results:
                poi = result.get("poi", {})
                address = result.get("address", {})
                position = result.get("position", {})
                poi_list.append({
                    "name": poi.get("name", "Unknown"),
                    "address": address.get("freeformAddress", "No address available"),
                    "lat": position.get("lat"),
                    "lon": position.get("lon")
                })
            return poi_list
        else:
            print("Error fetching POI data:", response.status_code, response.text)
        return []

class AzureMapDirection:
    def __init__(self):
        self.subscription_key = AZURE_MAPS_SUBSCRIPTION_KEY
        self.endpoint = "https://atlas.microsoft.com/route/directions/json"
        self.api_version = "1.0"
    
    def get_directions(self, start_lat, start_lon, dest_lat, dest_lon, travel_mode="car"):
        query = f"{start_lat},{start_lon}:{dest_lat},{dest_lon}"
        params = {
            "api-version": self.api_version,
            "query": query,
            "subscription-key": self.subscription_key,
            "travelMode": travel_mode,
            "routeRepresentation": "polyline"  # Request encoded polyline
        }
        response = requests.get(self.endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print("Error fetching directions:", response.status_code, response.text)
        return None
    
    def generate_route_map(self, directions_json, start_lat, start_lon, dest_lat, dest_lon):
        try:
            # Extract the "points" data from the first leg.
            leg = directions_json["routes"][0]["legs"][0]
            polyline = leg["points"]
        except Exception as e:
            print("Error extracting polyline:", e)
            return None

        # Process the polyline based on its type.
        if isinstance(polyline, str):
            # Encoded polyline string.
            route_coords = decode_polyline(polyline)
        elif isinstance(polyline, dict):
            # Expecting a GeoJSON-like structure with "coordinates".
            if "coordinates" in polyline:
                # Coordinates are usually in [lon, lat] order.
                route_coords = [(coord[1], coord[0]) for coord in polyline["coordinates"]]
            else:
                print("Unexpected dict format for polyline:", polyline)
                return None
        elif isinstance(polyline, list):
            # Handle list formats.
            if len(polyline) > 0:
                first_item = polyline[0]
                if isinstance(first_item, list) and len(first_item) == 2:
                    # List of coordinate pairs in [lon, lat] order.
                    route_coords = [(coord[1], coord[0]) for coord in polyline]
                elif isinstance(first_item, (int, float)):
                    # Flat list of numbers: [lon, lat, lon, lat, ...]
                    if len(polyline) % 2 == 0:
                        route_coords = []
                        for i in range(0, len(polyline), 2):
                            route_coords.append((polyline[i+1], polyline[i]))
                    else:
                        print("Unexpected flat list format for polyline:", polyline)
                        return None
                else:
                    print("Unexpected list format for polyline:", type(first_item))
                    return None
            else:
                print("Empty list for polyline.")
                return None
        else:
            print("Unexpected format for polyline:", type(polyline))
            return None

        # Create a folium map centered between the start and destination.
        center_lat = (start_lat + dest_lat) / 2
        center_lon = (start_lon + dest_lon) / 2
        route_map = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        # Add markers for start and destination.
        folium.Marker(location=[start_lat, start_lon], popup="Start", icon=folium.Icon(color="green")).add_to(route_map)
        folium.Marker(location=[dest_lat, dest_lon], popup="Destination", icon=folium.Icon(color="red")).add_to(route_map)

        # Draw the route polyline.
        folium.PolyLine(locations=route_coords, color="blue", weight=5).add_to(route_map)
        return route_map

def main():
    # User enters their location in words.
    location_text = input("Enter your location (e.g., address or city): ").strip()
    if not location_text:
        print("Location cannot be empty.")
        return

    # Convert the address to coordinates.
    geocoder = AzureMapsGeocoder()
    user_lat, user_lon = geocoder.get_coordinates(location_text)
    if user_lat is None or user_lon is None:
        print("Unable to get coordinates for the provided location.")
        return
    print(f"Your location: {user_lat}, {user_lon}")

    # Ask for a category of place to search for.
    category = input("Enter the type of place you're looking for (e.g., restaurant, park): ").strip()
    if not category:
        print("Category cannot be empty.")
        return

    # Search for nearby points of interest.
    poi_search = AzureMapsPOISearch()
    poi_results = poi_search.search_poi(user_lat, user_lon, category)
    if not poi_results:
        print("No places found for the given category near your location.")
        return

    print(f"Nearby {category.title()}s:")
    for idx, poi in enumerate(poi_results):
        print(f"{idx + 1}. {poi['name']} - {poi['address']}")

    try:
        choice = int(input("Enter the number of the place you want directions for: ").strip())
        if choice < 1 or choice > len(poi_results):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input; please enter a number.")
        return

    destination = poi_results[choice - 1]
    dest_lat = destination['lat']
    dest_lon = destination['lon']
    print(f"You selected: {destination['name']} located at {destination['address']}")

    # Retrieve directions from the user's location to the chosen destination.
    direction_service = AzureMapDirection()
    directions = direction_service.get_directions(user_lat, user_lon, dest_lat, dest_lon, travel_mode="car")
    if not directions:
        print("Failed to retrieve directions.")
        return

    # Generate and display the route map.
    route_map = direction_service.generate_route_map(directions, user_lat, user_lon, dest_lat, dest_lon)
    if route_map:
        map_file = "route_map.html"
        route_map.save(map_file)
        abs_path = os.path.abspath(map_file)
        url = "file:///" + abs_path
        print(f"Route map saved to {abs_path}. Opening in your browser...")
        webbrowser.open(url)
    else:
        print("Failed to generate route map.")

if __name__ == "__main__":
    main()
