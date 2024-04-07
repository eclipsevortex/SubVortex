import json
import os
import requests
import bittensor as bt
from math import radians, sin, cos, sqrt, atan2

LOCLISATION_API = "https://api.country.is"

countries = {}


def get_localisation(country_code: str):
    """
    Get the longitude and latitude of the country
    """
    global countries
    if len(countries) == 0:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(current_dir, "..", "localisation.json")

        with open(file_path, "r") as f:
            countries = json.load(f)

    return countries.get(country_code)


def get_country(ip: str):
    """
    Get the country code of the ip
    """
    url = f"{LOCLISATION_API}/{ip}"

    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()

    return data["country"]


def compute_localisation_distance(lat1, lon1, lat2, lon2):
    """
    Compute the distance between two localisations using Haversine formula
    """
    distance = 0

    try:
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = 6371 * c  # Radius of the Earth in kilometers
        return distance
    except Exception as err:
        bt.logging.error(
            f"Could not compute the distance from {lat1}/{lon1} to {lat2}/{lon2}: {err}"
        )

    return distance
