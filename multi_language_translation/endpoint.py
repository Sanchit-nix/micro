from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from translation_service import TranslationService
from pathlib import Path
import shutil
import uuid
import os

router = APIRouter()
translator = TranslationService()

UPLOAD_DIR = Path("input_files")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/translate-text/")
async def translate_text(
    text: str = Form(...),
    src_lang: str = Form(...),
    tgt_lang: str = Form(...)
):
    result = translator.translate_text(text, src_lang, tgt_lang)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/translate-file/")
async def translate_file(
    file: UploadFile = File(...),
    src_lang: str = Form(...),
    tgt_lang: str = Form(...)
):

    if not file.filename.lower().endswith((".txt",)):
        raise HTTPException(status_code=400, detail="Only .txt files are supported.")

    input_filename = f"{uuid.uuid4().hex}_{file.filename}"
    input_path = UPLOAD_DIR / input_filename
    output_path = input_path.with_stem(input_path.stem + "_translated")

    try:
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = translator.translate_file(str(input_path), str(output_path), src_lang, tgt_lang)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result["error"])

        return FileResponse(
            path=str(output_path),
            media_type="application/octet-stream",
            filename=output_path.name
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {e}")
    finally:
        try:
            input_path.unlink()
        except Exception:
            pass


@router.get("/supported-languages/")
async def supported_languages():
    return translator.get_supported_languages()
