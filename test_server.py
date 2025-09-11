import requests
import json

# Test the server with a simple POST request
url = "http://127.0.0.1:8001/islr/predict"
data = []  # Empty data
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, data=json.dumps(data), headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
