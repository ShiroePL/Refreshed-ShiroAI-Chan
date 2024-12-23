import base64
import requests
import os

# Fetch your API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Encode your image
image_path = "test_vision_pic.png"  # Ensure this path is correct and the image exists
base64_image = encode_image(image_path)

# Prepare the headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# Create the payload
payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "What’s in this image?"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": f"data:image/png;base64,{base64_image}"
            }
          }
        ]
      }
    ],
    "max_tokens": 300
}

# Make the request and handle potential errors
try:
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60  # timeout in seconds
    )
    response.raise_for_status()  # Raise an HTTPError if an unsuccessful status code is returned
    print(response.json())  # Print the response if the request is successful
except requests.exceptions.Timeout:
    print("The request timed out. Please try again later or with a smaller image.")
except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")  # Print the HTTP error
except requests.exceptions.ConnectionError as conn_err:
    print(f"Connection error occurred: {conn_err}")  # Print the connection error
except requests.exceptions.RequestException as req_err:
    print(f"An error occurred: {req_err}")  # Print any other request-related error
except Exception as e:
    print(f"An unexpected error occurred: {e}")  # Print any other exceptions not related to the request
