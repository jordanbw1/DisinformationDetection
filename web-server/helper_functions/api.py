import requests
import json
from openai import OpenAI

def test_gemini_key(api_key):
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


def test_chatgpt_key(api_key):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {
        "role": "user",
        "content": "Test this for me"
        }
    ],
    temperature=1,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )

    return False, "Not implemented yet"