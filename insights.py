import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Inputs
file_path = "output/pages/3mcm3cathoi5eahjeq7e5tgessfktszioxyf4rnx2ug7ab3ilzvgwfyd.onion_573e53cb.txt"
SUMMARY_DIR = "output/summary"
os.makedirs(SUMMARY_DIR, exist_ok=True)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model = "gemini-2.0-flash"

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

# Read the .txt file
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
    url = lines[0].strip().replace("URL: ", "")
    raw_text = "".join(lines[2:]).strip()

prompt = build_prompt(raw_text, url)

# Generate response
try:
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    output_text = response.text.strip()

    # 🧼 Clean markdown if wrapped
    if output_text.startswith("```json"):
        output_text = output_text.replace("```json", "").replace("```", "").strip()

    # Parse and save JSON
    data = json.loads(output_text)

    json_filename = os.path.basename(file_path).replace(".txt", ".json")
    json_path = os.path.join(SUMMARY_DIR, json_filename)

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(data, jf, indent=2)

    print(f"[✓] Saved JSON: {json_path}")

except Exception as e:
    print(f"[!] Error saving summary: {e}")
