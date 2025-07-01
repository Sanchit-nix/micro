
import os
import time
from pathlib import Path
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

class ModelManager:
    def __init__(self, base_dir="ds_models"): 
        # Create the translation subdirectory within ds_models
        self.base_dir = Path(base_dir) / "translation"
        self.model_configs = {
            "indictrans2": {
                "en_to_indic": "ai4bharat/indictrans2-en-indic-dist-200M",
                "indic_to_en": "ai4bharat/indictrans2-indic-en-dist-200M"
            },
            "opus_mt": {
                "en_to_zh": "Helsinki-NLP/opus-mt-en-zh", 
                "zh_to_en": "Helsinki-NLP/opus-mt-zh-en"
            }
        }
        self._setup_directories()
    
    def _setup_directories(self):
        for model_type in self.model_configs.keys():
            (self.base_dir / model_type).mkdir(parents=True, exist_ok=True)
    
    def get_model_path(self, model_type, model_key):
        return {
            "model_id": self.model_configs[model_type][model_key],
            "cache_dir": str(self.base_dir / model_type / model_key.replace("_", "-"))
        }
    
    def ensure_model_available(self, model_type, model_key):
        config = self.get_model_path(model_type, model_key)
        cache_dir = config["cache_dir"]
        
        if not self._is_model_cached(cache_dir):
            self._download_model(config["model_id"], cache_dir)
        
        return cache_dir
    
    def _is_model_cached(self, cache_dir):
        path = Path(cache_dir)
        return path.exists() and any(path.iterdir())
    
    def _download_model(self, model_id, cache_dir):
        print(f"Downloading model: {model_id}")
        start_time = time.time()
        
        os.makedirs(cache_dir, exist_ok=True)
        
        tokenizer = AutoTokenizer.from_pretrained(
            model_id, 
            cache_dir=cache_dir,
            trust_remote_code=True
        )
        
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_id,
            cache_dir=cache_dir,
            trust_remote_code=True
        )
        
        tokenizer.save_pretrained(cache_dir)
        model.save_pretrained(cache_dir)
        
        elapsed = time.time() - start_time
        print(f"Model downloaded in {elapsed:.1f}s")
