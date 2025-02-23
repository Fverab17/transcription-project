import requests
import json
import os
from google.oauth2 import service_account

# Set your Google Cloud credentials
GOOGLE_CLOUD_CREDENTIALS = "/storage/emulated/0/Download/stt_key.json"

# Authenticate
credentials = service_account.Credentials.from_service_account_file(GOOGLE_CLOUD_CREDENTIALS)
access_token = credentials.token

# Select your audio file
audio_path = input("Enter the full path to the audio file: ").strip()

# Convert the audio file to base64
with open(audio_path, "rb") as f:
    audio_content = f.read()

# Prepare the API request
url = "https://speech.googleapis.com/v1/speech:recognize"
headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
data = {
    "config": {
        "encoding": "LINEAR16",
        "sampleRateHertz": 16000,
        "languageCode": "en-US"
    },
    "audio": {"content": audio_content.decode("ISO-8859-1")}
}

# Send the request
response = requests.post(url, headers=headers, json=data)
result = response.json()

# Print the transcription
print("Transcription:", result)