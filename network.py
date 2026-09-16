import requests


def is_connected():
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.RequestException:
        return False
