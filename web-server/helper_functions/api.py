import requests
import json

def test_key(api_key):
    # curl -H 'Content-Type: application/json' -d '{"contents":[{"parts":[{"text":"Write a story about a magic backpack"}]}]}' -X POST https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY
    
    # Replace 'YOUR_API_KEY' with your actual API key

    # Define the payload
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Write a story about a magic backpack"
                    }
                ]
            }
        ]
    }

    # Define headers
    headers = {
        'Content-Type': 'application/json'
    }

    # Define the API URL
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}'

    # Make POST request
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Check if there was an error
    if "error" in response.json():
        return False, "Bad API Key"
    return True, "Good API Key"
