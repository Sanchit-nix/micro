import torch
import time
import json
import csv
import os
from pathlib import Path
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit import IndicProcessor
from model_manager import ModelManager

class CoreTranslator:
    def __init__(self, models_dir="ds_models"):  
        self.device = self._get_device()
        self.model_manager = ModelManager(models_dir)  # \
        
        # IndicTrans2 setup
        self.ip = IndicProcessor(inference=True)
        self.indic_models = {}
        self.indic_tokenizers = {}
        
        # OPUS-MT setup
        self.opus_models = {}
        self.opus_tokenizers = {}
        
        # Language mappings
        self.supported_languages = {
            "eng_Latn": "English",
            "hin_Deva": "Hindi", 
            "urd_Arab": "Urdu",
            "zh": "Chinese"
        }
        
        self.direct_pairs = [
            ("eng_Latn", "hin_Deva"), ("hin_Deva", "eng_Latn"),
            ("eng_Latn", "urd_Arab"), ("urd_Arab", "eng_Latn"),
            ("eng_Latn", "zh"), ("zh", "eng_Latn")
        ]
    
    def _get_device(self):
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _load_indictrans_model(self, model_key):
        if model_key in self.indic_models:
            return self.indic_models[model_key], self.indic_tokenizers[model_key]
        
        cache_dir = self.model_manager.ensure_model_available("indictrans2", model_key)
        config = self.model_manager.get_model_path("indictrans2", model_key)
        
        tokenizer = AutoTokenizer.from_pretrained(
            config["model_id"], 
            cache_dir=cache_dir,
            trust_remote_code=True
        )
        
        dtype = torch.float16 if self.device != "cpu" else torch.float32
        model = AutoModelForSeq2SeqLM.from_pretrained(
            config["model_id"],
            cache_dir=cache_dir,
            trust_remote_code=True,
            torch_dtype=dtype
        ).to(self.device)
        
        model.eval()
        
        self.indic_models[model_key] = model
        self.indic_tokenizers[model_key] = tokenizer
        
        return model, tokenizer
    
    def _load_opus_model(self, model_key):
        if model_key in self.opus_models:
            return self.opus_models[model_key], self.opus_tokenizers[model_key]
        
        cache_dir = self.model_manager.ensure_model_available("opus_mt", model_key)
        config = self.model_manager.get_model_path("opus_mt", model_key)
        
        tokenizer = AutoTokenizer.from_pretrained(config["model_id"], cache_dir=cache_dir)
        
        dtype = torch.float16 if self.device != "cpu" else torch.float32
        model = AutoModelForSeq2SeqLM.from_pretrained(
            config["model_id"],
            cache_dir=cache_dir,
            torch_dtype=dtype
        ).to(self.device)
        
        model.eval()
        
        self.opus_models[model_key] = model
        self.opus_tokenizers[model_key] = tokenizer
        
        return model, tokenizer
    
    def _is_direct_supported(self, src_lang, tgt_lang):
        return (src_lang, tgt_lang) in self.direct_pairs
    
    def _is_multistep_supported(self, src_lang, tgt_lang):
        if self._is_direct_supported(src_lang, tgt_lang):
            return True
        
        can_src_to_eng = self._is_direct_supported(src_lang, "eng_Latn") or src_lang == "eng_Latn"
        can_eng_to_tgt = self._is_direct_supported("eng_Latn", tgt_lang) or tgt_lang == "eng_Latn"
        
        return can_src_to_eng and can_eng_to_tgt
    
    def _translate_indictrans(self, text, src_lang, tgt_lang):
        model_key = "en_to_indic" if src_lang == "eng_Latn" else "indic_to_en"
        model, tokenizer = self._load_indictrans_model(model_key)
        
        preprocessed = self.ip.preprocess_batch([text], src_lang=src_lang, tgt_lang=tgt_lang)
        
        inputs = tokenizer(
            preprocessed,
            padding="longest",
            truncation=True,
            max_length=256,
            return_tensors="pt"
        ).to(self.device)
        
        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_length=256,
                num_beams=5,
                length_penalty=0.8,
                early_stopping=True
            )
        
        decoded = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return self.ip.postprocess_batch([decoded], lang=tgt_lang)[0].strip()
    
    def _translate_opus(self, text, src_lang, tgt_lang):
        norm_src = "en" if src_lang == "eng_Latn" else src_lang
        norm_tgt = "en" if tgt_lang == "eng_Latn" else tgt_lang
        
        model_key = "en_to_zh" if norm_src == "en" else "zh_to_en"
        model, tokenizer = self._load_opus_model(model_key)
        
        inputs = tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_length=512,
                num_beams=4,
                length_penalty=0.8,
                early_stopping=True
            )
        
        return tokenizer.decode(generated_ids[0], skip_special_tokens=True).strip()
    
    def translate_direct(self, text, src_lang, tgt_lang):
        if src_lang == tgt_lang:
            return text
        
        if not text.strip():
            return text
        
        if "zh" in {src_lang, tgt_lang}:
            return self._translate_opus(text, src_lang, tgt_lang)
        else:
            return self._translate_indictrans(text, src_lang, tgt_lang)
    
    def translate_multistep(self, text, src_lang, tgt_lang):
        if self._is_direct_supported(src_lang, tgt_lang):
            return self.translate_direct(text, src_lang, tgt_lang)
        
        # Step 1: Source → English
        if src_lang != "eng_Latn":
            english_text = self.translate_direct(text, src_lang, "eng_Latn")
        else:
            english_text = text
        
        # Step 2: English → Target
        if tgt_lang != "eng_Latn":
            return self.translate_direct(english_text, "eng_Latn", tgt_lang)
        else:
            return english_text
    
    def translate_with_routing(self, text, src_lang, tgt_lang):
        if self._is_direct_supported(src_lang, tgt_lang):
            result = self.translate_direct(text, src_lang, tgt_lang)
            method = "direct"
        elif self._is_multistep_supported(src_lang, tgt_lang):
            result = self.translate_multistep(text, src_lang, tgt_lang)
            method = "multi_step"
        else:
            raise ValueError(f"Unsupported language pair: {src_lang} → {tgt_lang}")
        
        return {
            "translated_text": result,
            "translation_method": method,
            "source_language": src_lang,
            "target_language": tgt_lang,
            "status": "success"
        }
    
    def process_file(self, input_path, output_path, src_lang, tgt_lang, **kwargs):
        file_ext = Path(input_path).suffix.lower()
        
        if file_ext == ".txt":
            return self._process_txt_file(input_path, output_path, src_lang, tgt_lang)
        elif file_ext == ".json":
            return self._process_json_file(input_path, output_path, src_lang, tgt_lang, **kwargs)
        elif file_ext == ".csv":
            return self._process_csv_file(input_path, output_path, src_lang, tgt_lang, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _process_txt_file(self, input_path, output_path, src_lang, tgt_lang):
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        translated_lines = []
        for line in lines:
            if line.strip():
                result = self.translate_with_routing(line.strip(), src_lang, tgt_lang)
                translated_lines.append(result["translated_text"] + "\n")
            else:
                translated_lines.append(line)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(translated_lines)
        
        return {
            "status": "success",
            "input_file": input_path,
            "output_file": output_path,
            "lines_processed": len([l for l in lines if l.strip()])
        }
    
    def _process_json_file(self, input_path, output_path, src_lang, tgt_lang, **kwargs):
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        fields_translated = 0
        
        def translate_recursive(obj):
            nonlocal fields_translated
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and value.strip():
                        result = self.translate_with_routing(value, src_lang, tgt_lang)
                        obj[key] = result["translated_text"]
                        fields_translated += 1
                    elif isinstance(value, (dict, list)):
                        translate_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    translate_recursive(item)
        
        translate_recursive(data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "input_file": input_path,
            "output_file": output_path,
            "fields_translated": fields_translated
        }
    
    def _process_csv_file(self, input_path, output_path, src_lang, tgt_lang, **kwargs):
        translated_rows = []
        cells_translated = 0
        
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            for row in reader:
                translated_row = row.copy()
                for column, value in row.items():
                    if value and value.strip():
                        try:
                            result = self.translate_with_routing(value, src_lang, tgt_lang)
                            translated_row[column] = result["translated_text"]
                            cells_translated += 1
                        except:
                            translated_row[column] = value
                
                translated_rows.append(translated_row)
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            if translated_rows:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(translated_rows)
        
        return {
            "status": "success",
            "input_file": input_path,
            "output_file": output_path,
            "cells_translated": cells_translated
        }
    
    def get_supported_languages(self):
        return {
            "languages": self.supported_languages,
            "direct_pairs": self.direct_pairs,
            "multistep_available": True
        }
    
    def get_available_targets(self, src_lang, include_multistep=True):
        if include_multistep:
            available = []
            for lang in self.supported_languages.keys():
                if lang != src_lang and self._is_multistep_supported(src_lang, lang):
                    available.append(lang)
            return available
        else:
            return [tgt for src, tgt in self.direct_pairs if src == src_lang]
    
    def get_system_info(self):
        return {
            "device": self.device,
            "translation_systems": ["IndicTrans2", "OPUS-MT"],
            "direct_pairs": self.direct_pairs,
            "multistep_available": True
        }