from .base import STTProvider
from .twilio_stt import TwilioSTTProvider
from .google_stt import GoogleSTTProvider
from .azure_stt import AzureSTTProvider
from ...core.config import settings

def get_stt_provider() -> STTProvider:
    provider = settings.STT_PROVIDER.lower()
    if provider == "google":
        return GoogleSTTProvider()
    elif provider == "azure":
        return AzureSTTProvider()
    else:
        return TwilioSTTProvider()
