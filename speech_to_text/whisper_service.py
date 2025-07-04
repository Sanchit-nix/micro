from pathlib import Path
import whisper

class WhisperService:
    """
    A service for transcribing audio using OpenAI's Whisper model.
    """

    def __init__(self, model_name: str = "base", model_dir: Path = Path("ds_models/stt")):
        """
        Initialize the WhisperService with a specific model.
        Downloads the model to the given directory if not already available.
        """
        self.model_dir = model_dir
        self._ensure_model_directory(self.model_dir)
        self.model = whisper.load_model(model_name, download_root=str(self.model_dir))

    def _ensure_model_directory(self, path: Path) -> None:
        """
        Ensure the model directory exists.
        """
        path.mkdir(parents=True, exist_ok=True)

    def transcribe(self, audio_path: Path) -> str:
        """
        Transcribes the given audio file and returns the text.
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        result = self.model.transcribe(str(audio_path))
        return result.get("text", "")
