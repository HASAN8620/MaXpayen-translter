import os
import re
import json
import time
from googletrans import Translator

input_file = "american.oxt"
output_file = "american_roman.oxt"
checkpoint_file = "translation_checkpoint.json"

# Google Translator initialize kar rahe hain (Bina kisi API key ke!)
translator = Translator()

def translate_line(text):
    try:
        # Game ke tags (~z~, ~w~ waghera) bachane ke liye text ko todna
        parts = re.split(r'(~[a-zA-Z]~)', text)
        translated_parts = []
        
        for part in parts:
            if re.match(r'~[a-zA-Z]~', part):
                translated_parts.append(part) # Tag ko waise hi rakho
            elif part.strip():
                # English se Urdu translate karna
                res = translator.translate(part, src='en', dest='ur')
                
                # 'pronunciation' mein Google Translate ki Roman Urdu hoti hai 
                roman = res.pronunciation if res.pronunciation else res.text
                if roman:
                    translated_parts.append(roman)
                else:
                    translated_parts.append(part)
            else:
                translated_parts.append(part) # Spaces waghera ko waise hi rakho
                
        return "".join(translated_parts)
    except Exception as e:
        print(f"\n⚠️ Translation error: {e}", flush=True)
        return None

if os.path.exists(input_file):
    print(f"📁 Reading file: {input_file}", flush=True)
    saved_data = {}
    
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        print(f"🔄 Checkpoint Loaded: {len(saved_data)} lines pehle se translate ho chuki hain.", flush=True)

    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        all_lines = f.readlines()

    total = 0
    translated_in_this_run = 0

    print("🚀 Google Translate se translation shuru ho rahi hai (No API needed)...", flush=True)

    for idx, line in enumerate(all_lines):
        if re.search(r'=\s*~(z|w)~', line):
            total += 1
            key = line.split('=', 1)[0].strip()
            original_text = line.split('=', 1)[1].strip()
            
            if key not in saved_data:
                print(f"⏳ Translating ({len(saved_data)+1}): {key}...", end=" ", flush=True)
                roman_urdu = translate_line(original_text)
                
                if roman_urdu:
                    saved_data[key] = roman_urdu
                    translated_in_this_run += 1
                    print(f"✅", flush=True)
                    
                    # Har 10 lines ke baad save karo taake koi data miss na ho
                    if translated_in_this_run % 10 == 0:
                        with open(checkpoint_file, "w", encoding="utf-8") as cf:
                            json.dump(saved_data, cf, ensure_ascii=False, indent=2)
                    
                    # Google humein block na kare, isliye 1 second ka pause
                    time.sleep(1.0)
                else:
                    print(f"❌ Failed. 5 second wait kar ke agay barh rahe hain...", flush=True)
                    time.sleep(5)
                    
    # Aakhri bacha hua data save karna
    with open(checkpoint_file, "w", encoding="utf-8") as cf:
        json.dump(saved_data, cf, ensure_ascii=False, indent=2)

    # File Rebuild karna
    print("\n🔨 Rebuilding american_roman.oxt file...", flush=True)
    count = 0
    with open(output_file, "w", encoding="utf-8") as out:
        for line in all_lines:
            if re.search(r'=\s*~(z|w)~', line):
                k = line.split('=', 1)[0].strip()
                if k in saved_data:
                    out.write(f"{k} = {saved_data[k]}\n")
                    count += 1
                else:
                    out.write(line)
            else:
                out.write(line)
            
    print(f"\n🎉 SUCCESS! {count} lines Google Translate ke zariye convert ho gayin!", flush=True)
else:
    print(f"❌ Error: '{input_file}' file repository mein nahi mili.", flush=True)
