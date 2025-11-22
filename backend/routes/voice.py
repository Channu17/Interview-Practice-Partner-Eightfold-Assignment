from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from voice import generate_tts_audio, transcribe_audio

router = APIRouter()


@router.post("/voice-to-text")
async def voice_to_text(file: UploadFile = File(...)):
    payload = await file.read()
    transcript = transcribe_audio(payload, file.filename, file.content_type)
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to transcribe audio",
        )
    return {"transcript": transcript}


class TextToVoiceRequest(BaseModel):
    text: str


@router.post("/text-to-voice")
def text_to_voice(body: TextToVoiceRequest):
    audio_path = generate_tts_audio(body.text)
    if audio_path is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to generate audio",
        )
    return FileResponse(audio_path, media_type="audio/mpeg", filename=audio_path.name)
