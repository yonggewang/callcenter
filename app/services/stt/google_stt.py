import json
import base64
import asyncio
from typing import Any
from .base import STTProvider
from google.cloud import speech
from google.api_core.exceptions import GoogleAPIError
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

# Note: Requires GOOGLE_APPLICATION_CREDENTIALS to be set in env

class GoogleSTTProvider(STTProvider):
    def get_initial_twiml(self, prompt: str, callback_url: str) -> str:
        # callback_url in this context would be the wss:// logic
        # But we need a separate HTTP endpoint url for passing to the Stream?
        # Actually Twilio Stream connects to a URL we specify.
        # So we return TwiML that tells Twilio to connect to our WS endpoint.
        
        # We assume callback_url passed here is the WEBSOCKET URL (wss://...)
        
        response = VoiceResponse()
        response.say(prompt)
        connect = Connect()
        stream = Stream(url=callback_url)
        connect.append(stream)
        response.append(connect)
        return str(response)

    async def process_stream(self, websocket: Any, stream_sid: str):
        client = speech.SpeechAsyncClient()
        
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
            sample_rate_hertz=8000,
            language_code="en-US",
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True
        )

        async def request_generator():
            async for message in websocket.iter_text():
                data = json.loads(message)
                if data['event'] == 'media':
                    audio_chunk = base64.b64decode(data['media']['payload'])
                    yield speech.StreamingRecognizeRequest(audio_content=audio_chunk)
                elif data['event'] == 'stop':
                    break

        try:
            requests = request_generator()
            responses = await client.streaming_recognize(config=streaming_config, requests=requests)
            
            async for response in responses:
                if not response.results:
                    continue
                result = response.results[0]
                if not result.alternatives:
                    continue
                
                transcript = result.alternatives[0].transcript
                if result.is_final:
                    # Logic to handle final result -> 
                    # send back to call control?
                    # For this demo, we print. In real app, we might send a message back or update DB state
                    print(f"Google STT Final: {transcript}")
                    # Typically we'd close the stream or signal the main loop
        except Exception as e:
            print(f"Error in Google STT: {e}")
