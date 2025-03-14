import os
from dotenv import load_dotenv
import serpapi
import requests

load_dotenv()

# Load the SerpAPI key for Google Maps queries.
serp_api_key = os.getenv('SERPAPI_KEY')
client = serpapi.Client(api_key=serp_api_key)

# Load your Azure Maps subscription key for geocoding.
results= client.search({
    'engine': 'google_maps',
    'q': 'restaurants',
    'type': 'search',
    'll': '@40.712776,-74.005974,20z',
})
print(results)