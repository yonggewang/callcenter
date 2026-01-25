from fastapi import FastAPI, Request, WebSocket, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from .core.config import settings
from .services.stt import get_stt_provider
from .models.database import get_restaurant_by_phone
import logging
import os

app = FastAPI(title=settings.PROJECT_NAME)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- API Routes ---

@app.get("/api/status")
async def root():
    return {"message": "Restaurant AI Call Center is running"}

@app.post("/voice")
async def voice_entry(request: Request, To: str = Form(...)):
    """
    Entry point for incoming calls.
    """
    logger.info(f"Incoming call to {To}")
    
    restaurant = get_restaurant_by_phone(To)
    if not restaurant:
        from twilio.twiml.voice_response import VoiceResponse
        resp = VoiceResponse()
        resp.say("Sorry, we could not find a restaurant for this number.")
        return Response(content=str(resp), media_type="application/xml")

    provider = get_stt_provider()
    
    base_url = settings.SERVER_HOST
    prompt = f"Welcome to {restaurant.name}. What would you like to order?"
    
    if settings.STT_PROVIDER == "twilio":
        callback_url = f"{base_url}/voice/transcribe"
        twiml = provider.get_initial_twiml(prompt, callback_url)
    else:
        # Google or Azure need WebSocket URL
        # Replace https:// with wss://
        ws_url = base_url.replace("https://", "wss://").replace("http://", "ws://")
        stream_url = f"{ws_url}/ws"
        twiml = provider.get_initial_twiml(prompt, stream_url)
        
    return Response(content=twiml, media_type="application/xml")

@app.post("/voice/transcribe")
async def voice_transcribe(SpeechResult: str = Form(...)):
    """
    Callback for Twilio <Gather> (Built-in STT)
    """
    logger.info(f"Twilio STT Result: {SpeechResult}")
    
    from twilio.twiml.voice_response import VoiceResponse
    resp = VoiceResponse()
    resp.say(f"I heard you say: {SpeechResult}. One moment while I simulate processing your order.")
    # Here logic to add to cart, asking next question...
    return Response(content=str(resp), media_type="application/xml")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected for Audio Stream")
    
    provider = get_stt_provider()
    try:
        await provider.process_stream(websocket, "stream_id_placeholder")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# --- Static Web Content ---
# This allows hosting normal web content in the /static folder
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    logger.warning(f"Static directory not found at {static_dir}. 'Normal web content' hosting disabled.")
