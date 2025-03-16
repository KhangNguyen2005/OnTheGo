import os
from dotenv import load_dotenv
import serpapi
import requests
import json
from flask import Flask, render_template, request, redirect, url_for, flash

load_dotenv()

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to a secure key

# Initialize SerpAPI client
serp_api_key = os.getenv('SERPAPI_KEY')
client = serpapi.Client(api_key=serp_api_key)

# Azure Maps Subscription Key (set via .env or use the default provided here)
SUBSCRIPTION_KEY = os.getenv('AZURE_MAPS_SUBSCRIPTION_KEY', '9FeaTsMg7fH5DgcchS5AtICBBNTWnuoBHNG4H0a3OLzkxTeY9lHnJQQJ99BCACYeBjF6fAFpAAAgAZMP2bXk')

# Simple mapping for common country names to ISO 3166-1 alpha-2 codes.
country_mapping = {
    "usa": "US",
    "united states": "US",
    "united states of america": "US",
    "canada": "CA"
    # Extend this mapping as needed.
}

def get_country_code(country):
    return country_mapping.get(country.lower().strip(), country.upper())

def get_coordinates(country, state, city=None, address=None):
    country_code = get_country_code(country)
    structured_url = "https://atlas.microsoft.com/search/address/structured/json"
    params = {
        "subscription-key": SUBSCRIPTION_KEY,
        "api-version": "1.0",
        "countryCode": country_code,
        "countrySubdivision": state
    }
    if city:
        params["municipality"] = city
    if address:
        params["streetName"] = address

    response = requests.get(structured_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("results"):
            position = data["results"][0]["position"]
            return position["lat"], position["lon"]
        else:
            raise Exception("No matching address found.")
    else:
        raise Exception(f"Address API error: {response.status_code}")

def generate_ll_param(lat, lon, zoom=25):
    return f"@{lat},{lon},{zoom}z"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        country = request.form.get('country', '').strip()
        state = request.form.get('state', '').strip()
        city = request.form.get('city', '').strip()
        address = request.form.get('address', '').strip()
        amenity = request.form.get('amenity', 'restaurant').strip()

        if not country or not state:
            flash("Country and state/province are required fields.", "error")
            return redirect(url_for('index'))

        try:
            # Get the latitude and longitude using the Azure Maps API
            lat, lon = get_coordinates(country, state, city if city else None, address if address else None)
            ll_param = generate_ll_param(lat, lon)
            
            # Perform a nearby search with SerpAPI
            params = {
                'engine': 'google_maps', 
                'q': amenity, 
                'type': 'search', 
                'll': ll_param
            }
            results = client.search(params)
            
            # Extract location details
            if "places_results" in results:
                locations = results["places_results"][:5]
            elif "local_results" in results:
                locations = results["local_results"][:5]
            elif "results" in results:
                locations = results["results"][:5]
            else:
                locations = []
            
            reduced_locations = []
            for loc in locations:
                reduced_locations.append({
                    "Name": loc.get("title"),
                    "Address": loc.get("address"),
                    "Rating": loc.get("rating"),
                    "Price": loc.get("price"),
                    "Opening Hour": loc.get("hours", loc.get("open_state"))
                })
            
            full_location = f"{address + ', ' if address else ''}{city + ', ' if city else ''}{state}, {country}"
            
            return render_template('result.html', 
                                   full_location=full_location, 
                                   lat=lat, 
                                   lon=lon, 
                                   locations=reduced_locations, 
                                   amenity=amenity)
        except Exception as e:
            flash(str(e), "error")
            return redirect(url_for('index'))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
