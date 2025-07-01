import os
from pathlib import Path
from core_translator import CoreTranslator

class TranslationService:
    def __init__(self):
        self.models_dir = self._setup_models_directory()
        self.core_translator = CoreTranslator(self.models_dir)
    
    def _setup_models_directory(self):
        models_dir = "ds_models/translation"  
        Path(models_dir).mkdir(parents=True, exist_ok=True)
        return models_dir
    
    def translate_text(self, text: str, src_lang: str, tgt_lang: str) -> dict:
        try:
            if not text.strip():
                return {"status": "error", "error": "Empty text provided"}
            
            if src_lang == tgt_lang:
                return {
                    "translated_text": text,
                    "translation_method": "none",
                    "source_language": src_lang,
                    "target_language": tgt_lang,
                    "status": "success"
                }
            
            result = self.core_translator.translate_with_routing(text, src_lang, tgt_lang)
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "source_language": src_lang,
                "target_language": tgt_lang
            }
    
    def translate_file(self, input_path: str, output_path: str, src_lang: str, tgt_lang: str, **kwargs) -> dict:
        try:
            if not os.path.exists(input_path):
                return {"status": "error", "error": f"Input file not found: {input_path}"}
            
            result = self.core_translator.process_file(input_path, output_path, src_lang, tgt_lang, **kwargs)
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "input_file": input_path
            }
    
    def get_supported_languages(self) -> dict:
        return self.core_translator.get_supported_languages()