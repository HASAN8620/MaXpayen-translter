import os
import re
import json
import time
import requests

KEYS_ENV = os.environ.get("OPENROUTER_API_KEYS", "")
API_KEYS = [k.strip() for k in KEYS_ENV.split(",") if k.strip()]

if not API_KEYS:
    print("❌ Error: OPENROUTER_API_KEYS Secret nahi mila.")
    exit(1)

current_key_idx = 0
current_model_idx = 0

# 4 Best Free Models (Agar ek fail hoga toh doosra chalega)
FREE_MODELS = [
    "huggingfaceh4/zephyr-7b-beta:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "google/gemma-2-9b-it:free",
    "meta-llama/llama-3-8b-instruct:free"
]

def get_current_key():
    return API_KEYS[current_key_idx]

def get_current_model():
    return FREE_MODELS[current_model_idx]

def switch_key():
    global current_key_idx
    current_key_idx = (current_key_idx + 1) % len(API_KEYS)
    print(f"\n🔄 [KEY SWITCH] Key #{current_key_idx + 1} par switch ho gaye hain...", flush=True)

def switch_model():
    global current_model_idx
    current_model_idx = (current_model_idx + 1) % len(FREE_MODELS)
    print(f"\n🔄 [MODEL SWITCH] Naya model try kar rahe hain: {FREE_MODELS[current_model_idx]}", flush=True)

input_file = "american.oxt"
output_file = "american_roman.oxt"
checkpoint_file = "translation_checkpoint.json"
batch_size = 20

SYSTEM_PROMPT = """
You are an expert game dialogue translator.
Translate the English text into natural, conversational, and very easy "WhatsApp-style Roman Urdu" (Latin script) that a common gamer can easily read (e.g., 'Main yahan fasa hua hoon').

STRICT RULES:
1. Preserve ALL formatting tags (~z~, ~w~, ~n~, ~a~, ~g~, ~b~) EXACTLY as they appear at the start or inside the line. Do NOT alter them.
2. Return ONLY a valid JSON object matching the exact input keys provided. No extra text or code blocks.
3. Translate EVERY line into Roman Urdu. Do NOT return text in English.
4. Keep the tone gritty, natural, and suited for an action game.
"""

def translate_batch(batch_dict):
    url = "https://openrouter.ai/api/v1/chat/completions"
    prompt = f"Translate these dialogue values to Roman Urdu:\n{json.dumps(batch_dict, ensure_ascii=False)}"
    
    max_attempts = len(API_KEYS) * len(FREE_MODELS)
    
    for attempt in range(max_attempts):
        payload = {
            "model": get_current_model(), 
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }

        headers = {
            "Authorization": f"Bearer {get_current_key()}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                res_json = response.json()
                content = res_json['choices'][0]['message']['content']
                
                if content.startswith("```json"):
                    content = content[7:-3]
                elif content.startswith("
