import os
import json
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model = "gemini-2.0-flash"

PAGES_DIR = "output/pages"
SUMMARY_DIR = "output/summary"
FAILED_DIR = os.path.join(SUMMARY_DIR, "failed")
os.makedirs(SUMMARY_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)

def build_prompt(text, url):
    return f"""
You are a darknet/darkweb intelligence analyst.

Given the raw content of a darknet page, analyze and return a report in JSON format with the following keys:

- title
- url
- summary
- risk_assessment: {{ score, level, category }}
- keywords
- pii: {{ names, emails, websites, contact_numbers }}
- action_plan

Darknet page content:
{text}

Page URL:
{url}

⚠️ Please return only valid JSON. Do not use markdown, triple backticks, or any explanation. The response must start with {{ and end with }}.
"""

# 🚀 Process all .txt files
for filename in os.listdir(PAGES_DIR):
    if not filename.endswith(".txt"):
        continue

    txt_path = os.path.join(PAGES_DIR, filename)
    json_path = os.path.join(SUMMARY_DIR, filename.replace(".txt", ".json"))
    fail_path = os.path.join(FAILED_DIR, filename.replace(".txt", ".FAILED.txt"))

    # Skip already processed or previously failed
    if os.path.exists(json_path):
        print(f"[✔] Skipping (exists): {filename}")
        continue
    if os.path.exists(fail_path):
        print(f"[✘] Skipping (previously failed): {filename}")
        continue

    try:
        # Extract content
        with open(txt_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            url = lines[0].strip().replace("URL: ", "")
            raw_text = "".join(lines[2:]).strip()

        prompt = build_prompt(raw_text, url)

        # Call Gemini
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        output_text = response.text.strip()

        # Clean wrapping if needed
        if output_text.startswith("```json"):
            output_text = output_text.replace("```json", "").replace("```", "").strip()

        # Try to parse JSON
        data = json.loads(output_text)
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(data, jf, indent=2)

        print(f"[✓] Saved: {json_path}")

    except Exception as e:
        print(f"[!] Failed on {filename}: {e}")
        with open(fail_path, "w", encoding="utf-8") as fail_file:
            fail_file.write(output_text if 'output_text' in locals() else str(e))

    # ✅ Delay to avoid rate limit
    time.sleep(3)
