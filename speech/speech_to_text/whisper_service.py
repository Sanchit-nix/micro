import whisper
from pathlib import Path

class WhisperService:
    def __init__(self, model_name="base"):
        self.model = whisper.load_model(model_name,download_root="ds_models/sst")

    def transcribe(self, audio_path: Path) -> str:
        result = self.model.transcribe(str(audio_path))
        return result["text"]
