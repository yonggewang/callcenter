from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import logging

class Settings(BaseSettings):
    PROJECT_NAME: str = "Quantum CA AI Call Center"
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    
    # App Config
    # STT_PROVIDER can be: "twilio", "google", "azure", "openai"
    STT_PROVIDER: str = "twilio" 
    
    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Azure
    AZURE_SPEECH_KEY: Optional[str] = None
    AZURE_SPEECH_REGION: Optional[str] = None

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Server Host (for Twilio callbacks)
    SERVER_HOST: str = "https://quantumca.org"

    class Config:
        env_file = "/var/www/call_center_ai/.env"
        extra = "ignore"

settings = Settings()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Startup Configuration Logs (Printed to stdout for visibility in journalctl)
print(f"\n{'='*40}")
print(f"  CONF: STT Provider: {settings.STT_PROVIDER}")
print(f"  CONF: OpenAI Key:   {'Set' if settings.OPENAI_API_KEY else 'Missing'}")
print(f"  CONF: Google Key:   {settings.GOOGLE_APPLICATION_CREDENTIALS or 'Missing'}")
print(f"{'='*40}\n")
