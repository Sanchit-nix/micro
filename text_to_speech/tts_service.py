import os
from pathlib import Path
from langdetect import detect
from TTS.api import TTS

os.environ["COQUI_TOS_AGREED"] = "1"

SPEAKER_WAVS = {
    "British Male": "Voice/British_male.wav",
    "British Female": "Voice/British_female.wav",
    "Indian Male": "Voice/Indian_male.wav",
    "Indian Female": "Voice/Indian_female.wav"
}


class TTSService:
    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"):
        """
        Initialize the TTS service and prepare model directories.
        """
        self._setup_model_directory(Path("ds_models"))
        self.tts = TTS(model_name=model_name, progress_bar=False).to("cpu")

    def _setup_model_directory(self, model_dir: Path) -> None:
        """
        Ensure model directory exists.
        """
        model_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_output_filename(base: str = None) -> str:
        """
        Generate a unique output filename.
        """
        os.makedirs("output", exist_ok=True)
        if base:
            return f"output/output_{base}.wav"
        else:
            count = 1
            while os.path.exists(f"output/output_{count}.wav"):
                count += 1
            return f"output/output_{count}.wav"

    def synthesize_speech(self, text: str, selected_voice: str, output_path: str) -> None:
        """
        Synthesize speech using the selected voice and save to output_path.
        """
        speaker_wav = SPEAKER_WAVS.get(selected_voice)
        if not speaker_wav:
            raise ValueError(
                f"Unsupported voice: '{selected_voice}'. "
                f"Available voices: {', '.join(SPEAKER_WAVS.keys())}"
            )

        full_path = os.path.abspath(speaker_wav)

        if not os.path.exists(full_path):
            raise FileNotFoundError(
                f"Speaker WAV not found at path: {full_path}. "
                f"Make sure the WAV file exists inside the Docker image or mounted volume."
            )

        try:
            lang_code = detect(text)
            print(f"Detected Language: {lang_code}")
        except Exception as e:
            raise ValueError(f"Language detection failed: {e}")

        try:
            self.tts.tts_to_file(
                text=text.strip(),
                speaker_wav=full_path,
                language=lang_code,
                file_path=output_path
            )
            print(f"Audio saved to: {output_path}")
        except Exception as e:
            raise RuntimeError(f"Voice synthesis failed: {e}")
