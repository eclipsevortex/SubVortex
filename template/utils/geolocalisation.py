import requests

def get_localisation_details_of_ip(ip_address):
    # Replace 'your_access_token' with your actual access token if you have one
    access_token = 'd11352cf82f1d9'
    url = f'https://ipinfo.io/{ip_address}/json?token={access_token}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
        data = response.json()
        country = data.get('country')
        region = data.get('region')
        city = data.get('city')
        return ( country, region, city )
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None