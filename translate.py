import os
import re
import json
import time
import requests

# GitHub Secrets se keys uthana
KEYS_ENV = os.environ.get("OPENROUTER_API_KEYS", "")
API_KEYS = [k.strip() for k in KEYS_ENV.split(",") if k.strip()]

if not API_KEYS:
    print("❌ Error: OPENROUTER_API_KEYS Secret nahi mila.")
    exit(1)

current_key_idx = 0

def get_current_key():
    return API_KEYS[current_key_idx]

def switch_key():
    global current_key_idx
    old_idx = current_key_idx
    current_key_idx = (current_key_idx + 1) % len(API_KEYS)
    print(f"\n🔄 [KEY SWITCH] Key #{old_idx + 1} se Key #{current_key_idx + 1} par switch ho rahe hain...", flush=True)

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
    
    # Sab se stable free model use kar rahe hain
    payload = {
        "model": "google/gemma-2-9b-it:free", 
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    for attempt in range(len(API_KEYS) * 2):
        headers = {
            "Authorization": f"Bearer {get_current_key()}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=45)
            
            if response.status_code == 200:
                res_json = response.json()
                content = res_json['choices'][0]['message']['content']
                
                # Agar AI markdown mein JSON bhej de toh usay saf karna
                if content.startswith("```json"):
                    content = content[7:-3]
                elif content.startswith("```"):
                    content = content[3:-3]
                    
                parsed = json.loads(content.strip())
                
                first_key = list(batch_dict.keys())[0]
                if parsed.get(first_key) and parsed[first_key] != batch_dict[first_key]:
                    return parsed
                else:
                    print(" ⚠️ Untranslated text returned. Retrying...", end="", flush=True)
            elif response.status_code in [429, 402]: 
                switch_key()
                time.sleep(2)
            elif response.status_code == 404:
                # Agar 404 aaye toh exact error print karega
                print(f" ⚠️ HTTP 404 Error Detail: {response.text}", end="", flush=True)
                switch_key()
                time.sleep(2)
            else:
                print(f" ⚠️ HTTP {response.status_code}: {response.text}. Switching key...", end="", flush=True)
                switch_key()
                time.sleep(2)
                
        except Exception as e:
            print(f" ⚠️ Connection error: {str(e)}. Switching key...", end="", flush=True)
            switch_key()
            time.sleep(2)
            
    return None

if os.path.exists(input_file):
    print(f"📁 Reading file: {input_file}", flush=True)
    saved_data = {}
    
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        print(f"🔄 Checkpoint Loaded: {len(saved_data)} lines pehle se complete hain.", flush=True)

    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        all_lines = f.readlines()

    pending_batch = {}
    total_dialogues = 0

    for idx, line in enumerate(all_lines):
        if re.search(r'=\s*~(z|w)~', line):
            total_dialogues += 1
            key = line.split('=', 1)[0].strip()
            
            if key in saved_data:
                continue

            text = line.split('=', 1)[1].strip()
            pending_batch[key] = text

            if len(pending_batch) >= batch_size:
                print(f"Translating... ({len(saved_data)}/{total_dialogues} lines done)", end="", flush=True)
                res = translate_batch(pending_batch)
                
                if res:
                    for k, v in res.items():
                        saved_data[k] = v
                    
                    with open(checkpoint_file, "w", encoding="utf-8") as cf:
                        json.dump(saved_data, cf, ensure_ascii=False, indent=2)
                    print(" [Saved]", flush=True)
                else:
                    print(" [Batch Failed - Skipped]", flush=True)
                
                pending_batch = {}
                time.sleep(1.0)

    # Remaining Batch
    if pending_batch:
        res = translate_batch(pending_batch)
        if res:
            for k, v in res.items():
                saved_data[k] = v
            with open(checkpoint_file, "w", encoding="utf-8") as cf:
                json.dump(saved_data, cf, ensure_ascii=False, indent=2)

    # Final File Rebuild
    print("\n🔨 Rebuilding american_roman.oxt file...", flush=True)
    translated_count = 0
    with open(output_file, "w", encoding="utf-8") as out:
        for line in all_lines:
            if re.search(r'=\s*~(z|w)~', line):
                key = line.split('=', 1)[0].strip()
                if key in saved_data:
                    out.write(f"{key} = {saved_data[key]}\n")
                    translated_count += 1
                else:
                    out.write(line)
            else:
                out.write(line)

    print(f"\n🎉 SUCCESS! File rebuild complete. Total {translated_count} lines translated successfully.", flush=True)
else:
    print(f"❌ Error: '{input_file}' file repository mein nahi mili.", flush=True)
