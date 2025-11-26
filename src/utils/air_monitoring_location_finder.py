import os
from dotenv import load_dotenv
import requests

# Load the .env file
load_dotenv()

def find_nearby_stations(latitude, longitude, radius=10000):
    url = "https://api.openaq.org/v3/locations"
    params = {
        'coordinates': f"{latitude},{longitude}",
        'radius': radius,
        'limit': 10,
        'sort': 'distance'  # Changed from 'order_by' to 'sort'
    }
    headers = {
        'Accept': 'application/json',
        'X-API-Key': os.getenv("OPEN_AQ_KEY")  # Include your API key
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

# NY coordinate
# latitude = 40.7042166653089
# longitude = -73.98696415012104

# # GLA
# latitude = 55.86588687325689
# longitude = -4.243144022737119

# # seattle
# latitude = 47.61736470806638
# longitude = -122.31305640979505

# tokyo
latitude = 35.66077151981672
longitude = 139.42421731458725

# Find nearby stations
stations = find_nearby_stations(latitude, longitude, radius=2500)

if stations:
    print("Nearby monitoring stations:")
    for station in stations:
        print(f"ID: {station['id']}, Name: {station['name']}, Distance: {station['distance']}m")
else:
    print("No stations found nearby.")
