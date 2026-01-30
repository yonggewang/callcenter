from fastapi import FastAPI, Request, WebSocket, Form, Response, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from .core.config import settings
from .services.stt import get_stt_provider
from .models.database import get_restaurant_by_phone, Restaurant
from .services.flow_manager import FlowManager
import logging

app = FastAPI(title=settings.PROJECT_NAME)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flow Manager
flow_manager = FlowManager()

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=FileResponse)
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Restaurant AI Call Center is running"}

@app.get("/status")
@app.get("/api/status")
async def status():
    return {"status": "online", "message": "Restaurant AI Call Center is running"}

@app.post("/voice")
async def voice_entry(request: Request, CallSid: str = Form(...), To: str = Form(...)):
    """
    Entry point for incoming calls.
    """
    logger.info(f"Incoming call {CallSid} to {To}")
    
    restaurant = get_restaurant_by_phone(To)
    if not restaurant:
        from twilio.twiml.voice_response import VoiceResponse
        resp = VoiceResponse()
        resp.say("Sorry, we could not find a restaurant for this number.")
        return Response(content=str(resp), media_type="application/xml")

    try:
        # Determine callback URL dynamically from request
        scheme = request.headers.get("x-forwarded-proto", "https")
        host = request.headers.get("host", settings.SERVER_HOST.replace("https://", ""))
        callback_url = f"{scheme}://{host}/voice/input"
        logger.info(f"Entry Callback: {callback_url}")
        
        twiml = flow_manager.start_call(CallSid, restaurant, callback_url)
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        import traceback
        logger.error(f"Error processing call: {e}")
        logger.error(traceback.format_exc())
        return Response(content="<Response><Say>An application error occurred.</Say></Response>", media_type="application/xml")

@app.post("/voice/input")
async def voice_input(request: Request, CallSid: str = Form(...), To: str = Form(...), SpeechResult: str = Form(None), Digits: str = Form(None), RecordingUrl: str = Form(None)):
    """
    Callback for Twilio <Gather> (Built-in STT)
    """
    # Updated to handle RecordingUrl for OpenAI Whisper
    user_input = SpeechResult or Digits
    
    if RecordingUrl:
        logger.info(f"Received RecordingUrl: {RecordingUrl}")
        try:
            from .services.transcriber import transcriber
            import os
            import uuid
            os.makedirs("temp_audio", exist_ok=True)
            file_id = f"{CallSid}_{uuid.uuid4().hex[:6]}"
            raw_audio_path = f"temp_audio/{file_id}_raw.wav"
            if transcriber.download_audio(RecordingUrl, raw_audio_path):
                transcript_text = transcriber.transcribe(raw_audio_path)
                logger.info(f"Whisper Transcript: {transcript_text}")
                if transcript_text:
                    user_input = transcript_text
            if os.path.exists(raw_audio_path): os.remove(raw_audio_path)
        except Exception as e:
            logger.error(f"Error in transcription flow: {e}")

    restaurant = get_restaurant_by_phone(To)
    if not restaurant:
         return Response(content="<Response><Say>System Error.</Say></Response>", media_type="application/xml")

    try:
        scheme = request.headers.get("x-forwarded-proto", "https")
        host = request.headers.get("host", settings.SERVER_HOST.replace("https://", ""))
        callback_url = f"{scheme}://{host}/voice/input"
        logger.info(f"Input from {CallSid}: {user_input} | Callback: {callback_url}")
        
        twiml = flow_manager.process_input(CallSid, user_input or "", restaurant, callback_url)
        logger.info(f"Returning TwiML for {CallSid}: {twiml}")
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        logger.error(f"Error in voice_input: {e}")
        return Response(content="<Response><Say>Processing error.</Say></Response>", media_type="application/xml")

# WebSocket kept for reference/integration
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected for Audio Stream")
    await websocket.close()
