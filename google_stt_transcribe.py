import os
import sys
import shutil
import subprocess
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def convert_to_wav(input_path, output_path):
    """Convert an audio file to WAV format using ffmpeg."""
    try:
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # FFmpeg command to convert audio to WAV
        cmd = ["ffmpeg", "-y", "-i", input_path, output_path]
        logging.info(f"Converting '{input_path}' to WAV format...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logging.error(f"FFmpeg conversion failed: {result.stderr}")
            return False

        logging.info(f"Successfully converted to '{output_path}'.")
        return True
    except Exception as e:
        logging.exception(f"Error during audio conversion: {e}")
        return False

def upload_to_gcs(local_path, gcs_uri):
    """Upload a file to Google Cloud Storage using gsutil."""
    try:
        if not os.path.isfile(local_path):
            raise FileNotFoundError(f"File to upload not found: {local_path}")

        cmd = ["gsutil", "cp", local_path, gcs_uri]
        logging.info(f"Uploading '{local_path}' to '{gcs_uri}'...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logging.error(f"GCS upload failed: {result.stderr}")
            return False

        logging.info("Upload to GCS successful.")
        return True
    except Exception as e:
        logging.exception(f"Error during file upload: {e}")
        return False

def transcribe_audio(gcs_uri, language_code="en-US"):
    """Transcribe an audio file in GCS using Google STT via gcloud CLI."""
    try:
        # Run the long-running recognition command
        cmd = [
            "gcloud", "ml", "speech", "recognize-long-running", gcs_uri,
            "--language-code", language_code, "--format", "json"
        ]
        logging.info(f"Transcribing audio at '{gcs_uri}' with language code '{language_code}'...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logging.error(f"Transcription failed: {result.stderr}")
            return None

        # Parse the JSON response
        response_data = json.loads(result.stdout)
        transcript_text = "\n".join(
            [res["alternatives"][0]["transcript"] for res in response_data.get("results", [])]
        )

        logging.info("Transcription completed successfully.")
        return transcript_text
    except Exception as e:
        logging.exception(f"Error during transcription: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 google_stt_transcribe.py <input_audio.m4a> [language_code]")
        sys.exit(1)

    input_file = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else "en-US"

    # Define output file paths
    base_name = os.path.splitext(os.path.basename(input_file))[0].replace(" ", "_")
    wav_file = os.path.join("/storage/emulated/0/Download", base_name + ".wav")

    # Determine Downloads directory
    downloads_dir = os.path.expanduser("~/storage/downloads")
    if not os.path.isdir(downloads_dir):
        downloads_dir = os.path.expanduser("~/Downloads")

    output_txt = os.path.join(downloads_dir, base_name + ".txt")
    gcs_path = f"gs://bucketfv/{base_name}.wav"

    # Step 1: Convert M4A to WAV
    if not convert_to_wav(input_file, wav_file):
        sys.exit(1)

    # Step 2: Upload WAV to Google Cloud Storage
    if not upload_to_gcs(wav_file, gcs_path):
        sys.exit(1)

    # Step 3: Transcribe the audio
    transcript_text = transcribe_audio(gcs_path, language_code=lang)
    if transcript_text is None:
        sys.exit(1)

    # Step 4: Save transcription to a text file in Downloads
    try:
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(transcript_text + "\n")
        logging.info(f"Transcription saved to: {output_txt}")
    except Exception as e:
        logging.exception(f"Failed to save transcription to file: {e}")
        sys.exit(1)