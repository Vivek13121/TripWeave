import os
import requests

AMADEUS_AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"


def get_amadeus_access_token():
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("Amadeus credentials not found in environment variables")

    response = requests.post(
        AMADEUS_AUTH_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    response.raise_for_status()
    return response.json()["access_token"]
