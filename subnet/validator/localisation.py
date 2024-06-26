import requests
import bittensor as bt
from math import radians, sin, cos, sqrt, atan2

MY_API_BASE_URL = "http://api.ip-from.com"
COUNTRY_IS_BASE_URL = "https://api.country.is"
IP_API_BASE_URL = "http://ip-api.com/json"
IPINFO_IO_BASE_URL = "https://ipinfo.io"

countries = {}


def get_country_by_my_api(ip: str):
    """
    Get the country code of the ip (use Maxwind and IpInfo)
    Reference: http://api.ip-from.com
    """
    url = f"{MY_API_BASE_URL}/{ip}"

    response = requests.get(url)

    if response.status_code != 200:
        return None, response.reason

    data = response.json()

    # New property to use
    country = data.get("country")

    # Depcreated
    country = country or data.get("maxmind_country")
    country = country or data.get("ipinfo_country")

    return (country, None)


def get_country_by_country_is(ip: str):
    """
    Get the country code of the ip
    Reference: https://country.is/
    """
    url = f"{COUNTRY_IS_BASE_URL}/{ip}"

    response = requests.get(url)

    if response.status_code != 200:
        return None, response.reason

    data = response.json()

    return data.get("country"), None


def get_country_by_ip_api(ip: str):
    """
    Get the country code of the ip
    Reference: https://ip-api.com/
    """
    url = f"{IP_API_BASE_URL}/{ip}"

    response = requests.get(url)

    if response.status_code != 200:
        return None, response.reason

    data = response.json()

    return data.get("countryCode"), None


def get_country_by_ipinfo_io(ip: str):
    """
    Get the country code of the ip
    Reference: https://ipinfo.io/
    """
    url = f"{IPINFO_IO_BASE_URL}/{ip}"

    response = requests.get(url)

    if response.status_code != 200:
        return None, response.reason

    data = response.json()

    return data.get("country"), None


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
