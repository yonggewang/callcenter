import os
import subprocess
import requests
import logging
from openai import OpenAI
from ..core.config import settings

logger = logging.getLogger(__name__)

class AudioTranscriber:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not set. Transcription will fail.")

    def download_audio(self, url: str, save_path: str) -> bool:
        """Downloads audio from a URL to a local file."""
        try:
            # Twilio URLs usually look like: https://api.twilio.com/2010-04-01/Accounts/{AC...}/Recordings/{RE...}
            # By default, these require Basic Auth (AccountSid, AuthToken) unless disabled in Twilio Console.
            
            auth = None
            if "twilio.com" in url:
                from ..core.config import settings
                auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                logger.info("Detected Twilio URL, using Basic Auth.")

            response = requests.get(url, auth=auth)
            
            logger.info(f"Download Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}, Size: {len(response.content)} bytes")
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                logger.error(f"Failed to download audio. Status: {response.status_code}, Response: {response.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return False

    def convert_audio(self, input_path: str, output_path: str) -> bool:
        """
        Converts audio to 16kHz mono WAV using ffmpeg.
        ffmpeg -i input.wav -ar 16000 -ac 1 output.wav
        """
        if not os.path.exists(input_path):
            return False
            
        try:
            command = [
                "ffmpeg",
                "-y", # Overwrite output
                "-i", input_path,
                "-ar", "16000",
                "-ac", "1",
                output_path
            ]
            # Capture output to avoid spamming logs unless error
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            logger.error("ffmpeg not found. Skipping conversion.")
            # If ffmpeg is missing, we might just copy the file or return False
            # Better to return False so caller knows to use original
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg conversion failed: {e}")
            return False

    def transcribe(self, file_path: str) -> str:
        """Transcribes the audio file using OpenAI Whisper."""
        if not self.client:
            return ""

        if not os.path.exists(file_path):
            logger.error(f"File not found for transcription: {file_path}")
            return ""

        try:
            with open(file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    language="en"
                )
            return transcript.text
        except Exception as e:
            logger.error(f"OpenAI Transcription error: {e}")
            return ""

# Global instance
transcriber = AudioTranscriber()
