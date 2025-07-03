import os
from pathlib import Path
from langdetect import detect
from TTS.api import TTS

os.environ["COQUI_TOS_AGREED"] = "1"

SPEAKER_WAVS = {
    "British Male": "Voice/British_male.wav",
    "British Female": "Voice/British_female.wav",
    "Indian Male": "Voice/Indian_male.wav",
    "Indian Female": "Voice/hi_female.wav"
}

class TTSService:
    def __init__(self, model_name="tts_models/multilingual/multi-dataset/xtts_v2"):
        self.tts = TTS(model_name=model_name, progress_bar=False).to("cpu")
        self.model = TTS.load_model(model_name,download_root="ds_models/tts")

    def get_output_filename(base=None):
        os.makedirs("output", exist_ok=True)
        if base:
            return f"output/output_{base}.wav"
        else:
            count = 1
            while os.path.exists(f"output/output_{count}.wav"):
                count += 1
            return f"output/output_{count}.wav"

    def synthesize_speech(self,text: str, selected_voice: str, output_path: str):
        try:
            lang_code = detect(text)
            print(f"🌐 Detected Language: {lang_code}")
        except Exception as e:
            raise ValueError(f"Language detection failed: {e}")

        speaker_wav = SPEAKER_WAVS.get(selected_voice)
        if not speaker_wav or not os.path.isfile(speaker_wav):
            raise FileNotFoundError(f"Voice not found: {speaker_wav}")

        try:
            self.tts.tts_to_file(
                text=text.strip(),
                speaker_wav=speaker_wav,
                language=lang_code,
                file_path=output_path
            )
            print(f"\n✅ Audio saved to: {output_path}")
        except Exception as e:
            raise RuntimeError(f"Voice synthesis failed: {e}")
