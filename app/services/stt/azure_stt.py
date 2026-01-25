import json
import base64
import os
from typing import Any
from .base import STTProvider
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

# Azure SDK imports
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech.audio import PushAudioInputStream, AudioStreamFormat

class AzureSTTProvider(STTProvider):
    def get_initial_twiml(self, prompt: str, callback_url: str) -> str:
        response = VoiceResponse()
        response.say(prompt)
        connect = Connect()
        stream = Stream(url=callback_url) # wss:// endpoint
        connect.append(stream)
        response.append(connect)
        return str(response)

    async def process_stream(self, websocket: Any, stream_sid: str):
        # Retrieve keys from env or config
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        service_region = os.getenv("AZURE_SPEECH_REGION")
        
        if not speech_key or not service_region:
            print("Azure credentials missing.")
            return

        # Setup Azure Audio Stream
        # Twilio sends mulaw 8000Hz
        format = AudioStreamFormat(samples_per_second=8000, bits_per_sample=8, channels=1, wave_stream_format=speechsdk.AudioStreamWaveFormat.MULAW)
        stream = PushAudioInputStream(stream_format=format)
        
        audio_config = speechsdk.audio.AudioConfig(stream=stream)
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Recognizing callback
        def recognized_cb(evt):
            print('Azure STT Final: {}'.format(evt.result.text))
            # Here you would typically trigger some event or state update logic

        speech_recognizer.recognized.connect(recognized_cb)
        speech_recognizer.start_continuous_recognition()

        try:
            async for message in websocket.iter_text():
                data = json.loads(message)
                if data['event'] == 'media':
                    audio_chunk = base64.b64decode(data['media']['payload'])
                    stream.write(audio_chunk)
                elif data['event'] == 'stop':
                    break
        finally:
            stream.close()
            speech_recognizer.stop_continuous_recognition()
