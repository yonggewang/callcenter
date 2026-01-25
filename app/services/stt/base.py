from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

class STTProvider(ABC):
    @abstractmethod
    def get_initial_twiml(self, prompt: str, callback_url: str) -> str:
        """
        Returns the TwiML to initiate the speech recognition.
        For Twilio: <Gather>
        For Google/Azure: <Connect><Stream>
        """
        pass

    @abstractmethod
    async def process_stream(self, websocket: Any, stream_sid: str):
        """
        Handles the WebSocket stream for audio processing (for Google/Azure).
        No-op for Twilio built-in.
        """
        pass
