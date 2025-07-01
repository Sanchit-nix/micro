from fastapi import APIRouter, UploadFile,File
from speech_to_text.whisper_service import WhisperService

router = APIRouter(tags=["speech_to_text"])
whisper_service = WhisperService()

@router.post("/speech-to-text/")
async def speech_to_text(file: UploadFile = File(...)):
    contents = await file.read()
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(contents)
    result = whisper_service.transcribe(temp_path)
    return {"text": result}