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

input_file = "american.oxt"
output_file = "american_roman.oxt"
checkpoint_file = "translation_checkpoint.json"
batch_size = 20

# 👉 ULTIMATE FIX: OpenRouter se aaj ke LIVE free models khud dhoondhna!
print("🔍 OpenRouter se aaj ke live FREE models dhoondh rahe hain...", flush=True)
MODELS = []
try:
    resp = requests.get("https://openrouter.ai/api/v1/models", timeout=15)
    if resp.status_code == 200:
        all_models = resp.json().get("data", [])
        for m in all_models:
            pricing = m.get("pricing", {})
            # Jinki qeemat strictly 0 hai, unko list mein daalo
            if pricing.get("prompt") in ["0", 0, "0.0"] and pricing.get("completion") in ["0", 0, "0.0"]:
                if m["id"].endswith(":free"): # Sirf free slugs
                    MODELS.append(m["id"])
except Exception as e:
    print(f"⚠️ Live models fetch karne mein masla: {e}", flush=True)

# Agar auto-fetch fail ho jaye toh yeh emergency backup models hain
if not MODELS:
    MODELS = [
        "google/gemma-2-9b-it:free",
        "huggingfaceh4/zephyr-7b-beta:free",
        "mistralai/mistral-7b-instruct:free"
    ]

print(f"✅ Yeh Free Models mile hain! Pehla try kar rahe hain: {MODELS[:3]}...", flush=True)

curr_key = 0
curr_model = 0

SYSTEM_PROMPT = """You are an expert game dialogue translator. Translate the English text into conversational "WhatsApp-style Roman Urdu". 
STRICT RULES:
1. Preserve ALL formatting tags (~z~, ~w~, ~n~, ~a~, ~g~, ~b~) EXACTLY. Do NOT alter them.
2. Return ONLY a valid JSON object matching the exact input keys. Do not say "Here is the translation".
3. Translate EVERY line into Roman Urdu."""

def translate_batch(batch_dict):
    global curr_key, curr_model
    url = "https://openrouter.ai/api/v1/chat/completions"
    prompt = f"Translate to Roman Urdu:\n{json.dumps(batch_dict, ensure_ascii=False)}"
    
    for attempt in range(15): # Max 15 attempts taake script jaldi haar na mane
        if curr_model >= len(MODELS):
            curr_model = 0 
            
        model_to_use = MODELS[curr_model]
        payload = {
            "model": model_to_use, 
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT}, 
                {"role": "user", "content": prompt}
            ], 
            "temperature": 0.2
        }
        
        headers = {
            "Authorization": f"Bearer {API_KEYS[curr_key]}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/HASAN8620/MaxPayen-translter", 
            "X-Title": "RomanUrduTranslator"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=40)
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                if content.startswith("```json"): content = content[7:-3]
                elif content.startswith("
