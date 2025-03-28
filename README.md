# OnTheGo
OnTheGo is an interactive travel planner application that integrates Azure Maps, SerpAPI, Azure Cosmos DB, and Azure OpenAI to provide users with personalized travel plans. The application allows users to search for locations, view nearby restaurants, hotels, and attractions, and even generate an optimized travel itinerary based on their input.

# Features
Interactive Map:
Uses Azure Maps to display an interactive map where users can search for locations by address or city, and see markers for restaurants, hotels, attractions, and custom filters.

# Data Fetching:
Leverages a Python script with SerpAPI to gather local data (restaurants, hotels, attractions) based on geographic coordinates. The data is filtered and stored in JSON files.

# AI-Driven Travel Planning:
Integrates Azure OpenAI via the ai_integration.py script to generate an optimal one-day travel plan. The plan is output as a JSON object containing separate itineraries for morning, afternoon, and evening.

# Cosmos DB Integration:
Stores and manages location and recommendation data using Azure Cosmos DB. The upload_cosmos.py script upserts documents into the database, ensuring data is available for further processing.

# Flask Backend:
Provides a RESTful API (in server.py) that serves the HTML page, handles location searches, fetches filtered data, processes user inputs, and triggers the travel plan generation workflow.

# Project Structure
InteractiveMap.html:
The frontend user interface built with HTML, JavaScript, and Azure Maps SDK. It allows users to enter search queries, apply filters, and display location markers on the map.

ai_integration.py:
Contains the integration with Azure OpenAI. This script reads a JSON dataset of top amenities and generates a travel plan based on a user query, outputting a valid JSON travel itinerary.

fetching_data.py:
A script that uses SerpAPI to search for local amenities (restaurants, hotels, tourist attractions) based on provided latitude, longitude, and a search query. It outputs results into a JSON file.

server.py:
Implements a Flask server that serves the frontend, exposes API endpoints for searching locations, fetching data, saving filter results, and generating travel plans. It also integrates with Azure Cosmos DB to upload and manage data.

upload_cosmos.py:
Uploads JSON data from various files (e.g., restaurant.json, hotel.json, attraction.json) into Azure Cosmos DB. This script ensures the latest recommendations are stored and ready for travel plan generation.

requirement.txt:
Lists all Python dependencies needed to run the project, including Flask, Azure SDKs, SerpAPI, and other supporting libraries.

README.md:
This file, providing an overview, setup instructions, and usage details for the project.

# Setup and Installation
Clone the Repository:
Clone the repository to your local machine.

Install Dependencies:
Ensure you have Python installed. Then install the required packages:

nginx
Copy
pip install -r requirement.txt
Environment Variables:
Create a .env file in the project root with the following variables:

AZURE_MAP_API – Your Azure Maps subscription key.

AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION – Credentials for Azure OpenAI.

COSMOS_ENDPOINT, COSMOS_DB_KEY, COSMOS_DATABASE, COSMOS_CONTAINER – Your Azure Cosmos DB connection details.

SERPAPI_KEY – Your SerpAPI key.

Run the Server:
Start the Flask server by running:

nginx
Copy
python server.py
The application should now be accessible at http://localhost:5000.

# Usage
Search and Explore:
Use the search bar in the Interactive Map to enter an address or city. Click on the map to select a location, and view nearby restaurants, hotels, and attractions.

Apply Filters:
Add filters to further refine search results (e.g., cuisine type, price range).

Generate Travel Plan:
Click on the "Generate Plan" button to create a personalized one-day itinerary. The plan is generated using AI and displayed as a JSON structure with morning, afternoon, and evening plans.

Data Management:
The backend automatically handles fetching data, saving filtered results, and uploading data to Cosmos DB to keep your recommendations up-to-date.

# Endpoints Overview
GET /:
Serves the InteractiveMap.html with the Azure Maps API key injected.

POST /search_location:
Fetches nearby restaurants and hotels based on provided latitude and longitude.

POST /fetching_data:
Retrieves data for a specific amenity type (e.g., restaurant) using SerpAPI.

GET /restaurant_data & /hotel_data:
Returns JSON data for restaurants and hotels respectively.

POST /attraction_data:
Fetches tourist attraction data based on location.

POST /save_result:
Saves the current filtered results.

POST /save_location:
Merges various location files and uploads data to Azure Cosmos DB.

POST /process_locations:
Processes merged location data with Azure OpenAI for further analysis.

POST /save_user_input:
Saves user input (address and filter) into Cosmos DB.

POST /generate_plan:
Executes the full workflow to generate an AI-driven travel plan.

Contributing
Khang Hoang Nguyen
Thanh Le 
Tien Phong Le
Minh Le

Contributions and suggestions are welcome. Feel free to open issues or submit pull requests for improvements.
