from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from translation_service import TranslationService
import os
import shutil
import uuid

router = APIRouter()
translator = TranslationService()

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
    input_filename = f"tmp/{uuid.uuid4().hex}_{file.filename}"
    output_filename = input_filename.replace(".", "_translated.", 1)
    os.makedirs("tmp", exist_ok=True)

    with open(input_filename, "wb") as f:
        shutil.copyfileobj(file.file, f)

    result = translator.translate_file(input_filename, output_filename, src_lang, tgt_lang)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return FileResponse(
        output_filename,
        media_type="application/octet-stream",
        filename=os.path.basename(output_filename)
    )

@router.get("/supported-languages/")
async def supported_languages():
    return translator.get_supported_languages()
