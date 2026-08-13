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

# Jo 2 models sab se zyada stable hain OpenRouter par
MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "qwen/qwen-2-7b-instruct:free"
]

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
    
    for attempt in range(4): # 4 attempts taake time zaya na ho
        payload = {
            "model": MODELS[curr_model], 
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
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                if content.startswith("```json"): content = content[7:-3]
                elif content.startswith("```"): content = content[3:-3]
                
                try:
                    parsed = json.loads(content.strip())
                    if parsed: return parsed
                except json.JSONDecodeError:
                    print(f"\n⚠️ Format Error. Retrying...", end="", flush=True)
            else:
                # ASAL ERROR YAHAN PRINT HOGA!
                print(f"\n⚠️ OPENROUTER ERROR {response.status_code} on {MODELS[curr_model]}:\n👉 {response.text}", flush=True)
                curr_model = (curr_model + 1) % len(MODELS)
                
        except Exception as e:
            print(f"\n⚠️ Connection Error: {e}", end="", flush=True)
            
        curr_key = (curr_key + 1) % len(API_KEYS)
        time.sleep(2)
        
    print("\n❌ Errors ki wajah se script ruk rahi hai. Upar OpenRouter ka Error Message parhein.")
    exit(1)

if os.path.exists(input_file):
    print(f"📁 Reading file: {input_file}", flush=True)
    saved_data = {}
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r", encoding="utf-8") as f: saved_data = json.load(f)
        print(f"🔄 Checkpoint Loaded: {len(saved_data)} lines done.", flush=True)

    with open(input_file, "r", encoding="utf-8", errors="ignore") as f: all_lines = f.readlines()
    pending_batch = {}
    total = 0

    for line in all_lines:
        if re.search(r'=\s*~(z|w)~', line):
            total += 1
            k = line.split('=', 1)[0].strip()
            if k not in saved_data:
                pending_batch[k] = line.split('=', 1)[1].strip()
                
            if len(pending_batch) >= batch_size:
                print(f"\n🚀 Translating batch... ({len(saved_data)}/{total})", flush=True)
                res = translate_batch(pending_batch)
                if res:
                    saved_data.update(res)
                    with open(checkpoint_file, "w", encoding="utf-8") as cf: 
                        json.dump(saved_data, cf, ensure_ascii=False, indent=2)
                    print("✅ [Batch Saved]", flush=True)
                pending_batch = {}
                time.sleep(1)

    if pending_batch:
        res = translate_batch(pending_batch)
        if res:
            saved_data.update(res)
            with open(checkpoint_file, "w", encoding="utf-8") as cf: 
                json.dump(saved_data, cf, ensure_ascii=False, indent=2)

    print("\n🔨 Rebuilding american_roman.oxt file...", flush=True)
    count = 0
    with open(output_file, "w", encoding="utf-8") as out:
        for line in all_lines:
            if re.search(r'=\s*~(z|w)~', line):
                k = line.split('=', 1)[0].strip()
                if k in saved_data:
                    out.write(f"{k} = {saved_data[k]}\n")
                    count += 1
                else: out.write(line)
            else: out.write(line)
            
    print(f"\n🎉 SUCCESS! {count} lines translated.", flush=True)
else:
    print(f"❌ Error: '{input_file}' file nahi mili.", flush=True)
