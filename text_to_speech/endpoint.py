from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import logging
import traceback
from typing import Optional
import uuid
from tts_service import TTSService  

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
tts_service = TTSService()  

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "British Male"
    language: Optional[str] = "en"

@router.post("/text-to-speech/")
async def text_to_speech(request: TTSRequest):
    try:
        logger.info(f"Received TTS request: {request.text[:50]}...")

        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        if len(request.text) > 5000:
            raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")

        filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
        output_path = os.path.join("output", filename)

        try:
            tts_service.synthesize_speech(
                text=request.text,
                selected_voice=request.voice,
                output_path=output_path
            )
            logger.info(f"TTS processing completed: {output_path}")
        except Exception as tts_error:
            logger.error(f"TTS processing failed: {tts_error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(tts_error))

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Audio file was not generated successfully")

        return FileResponse(
            path=output_path,
            media_type="audio/wav",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in text_to_speech: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
