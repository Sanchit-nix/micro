from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from text_to_speech.tts_service import TTSService

router = APIRouter(tags=["text_to_speech"])
tts_service = TTSService()

@router.post("/text-to-speech/")
async def text_to_speech(
    text: str = Query(..., description="Text to synthesize"),
    voice: str = Query(..., description="Voice to use (e.g. 'British Male')")
):
    try:
        output_path = tts_service.get_output_filename()
        tts_service.synthesize_speech(text=text, selected_voice=voice, output_path=output_path)
        return FileResponse(output_path, media_type="audio/wav", filename="output.wav")
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail="Voice synthesis failed.")
