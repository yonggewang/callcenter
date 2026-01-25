from .base import STTProvider
from twilio.twiml.voice_response import VoiceResponse, Gather

class TwilioSTTProvider(STTProvider):
    def get_initial_twiml(self, prompt: str, callback_url: str) -> str:
        response = VoiceResponse()
        gather = Gather(input='speech dtmf', action=callback_url, speechTimeout='auto')
        gather.say(prompt)
        response.append(gather)
        # Fallback if no input
        response.say("We didn't receive any input. Goodbye.")
        return str(response)

    async def process_stream(self, websocket: Any, stream_sid: str):
        # Twilio Built-in STT does not use the WebSocket stream method
        pass
