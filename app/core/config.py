from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Quantum CA AI Call Center"
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    
    # App Config
    # STT_PROVIDER can be: "twilio", "google", "azure"
    STT_PROVIDER: str = "twilio" 
    
    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS_JSON: Optional[str] = None
    
    # Azure
    AZURE_SPEECH_KEY: Optional[str] = None
    AZURE_SPEECH_REGION: Optional[str] = None
    
    # Server Host (for Twilio callbacks)
    SERVER_HOST: str = "https://quantumca.org"

    class Config:
        env_file = ".env"

settings = Settings()
