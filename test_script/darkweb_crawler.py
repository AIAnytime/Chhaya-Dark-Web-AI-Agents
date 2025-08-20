import subprocess
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import hashlib
from urllib.parse import urlparse

# Setup Tor session
session = requests.Session()
session.proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

def run_onionsearch(query):
    os.makedirs("output", exist_ok=True)
    safe_query = query.replace(" ", "_")
    output_file = f"output/onionsearch_{safe_query}.csv"
    print(f"[+] Running OnionSearch for: {query}")
    subprocess.run([
        "onionsearch",
        query,
        "--proxy", "127.0.0.1:9050",
        "--output", output_file,
        "--limit", "2"
    ])
    return output_file

def extract_onion_links_from_csv(file_path):
    links = []
    try_encodings = ['utf-8', 'windows-1252']

    for enc in try_encodings:
        try:
            with open(file_path, encoding=enc) as f:
                lines = f.readlines()
                first_row = lines[0].strip().split(',')
                print(f"[DEBUG] First row: {first_row}")

                # Detect if header is missing
                if '.onion' in first_row[-1]:
                    print("[!] No header detected. Injecting fallback header: engine,name,link")
                    lines.insert(0, "engine,name,link\n")

                reader = csv.DictReader(lines)
                for row in reader:
                    if '.onion' in row.get('link', ''):
                        links.append(row['link'])

                break  # success

        except UnicodeDecodeError:
            print(f"[!] Encoding {enc} failed. Trying next...")

    unique_links = list(set(links))
    print(f"[+] Extracted {len(unique_links)} .onion URLs")
    return unique_links

def extract_text_and_images(url):
    try:
        print(f"[-] Crawling: {url}")
        res = session.get(url, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        images = [img['src'] for img in soup.find_all('img') if img.get('src')]
        return {'url': url, 'text': text[:2000], 'images': images[:10]}
    except Exception as e:
        print(f"[!] Error processing {url}: {e}")
        return None

def save_single_result(entry):
    os.makedirs("output/pages", exist_ok=True)
    url = entry['url']
    hostname = urlparse(url).hostname or "unknown"
    uid = hashlib.md5(url.encode()).hexdigest()[:8]
    fname = f"{hostname}_{uid}.txt"
    path = os.path.join("output/pages", fname)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n\n")
        f.write("Text Content:\n")
        f.write(entry['text'] + "\n\n")
        f.write("Image Links:\n")
        for img in entry['images']:
            f.write(f"{img}\n")

    print(f"[✓] Saved: {path}")

def run_pipeline(query):
    csv_file = run_onionsearch(query)
    onion_links = extract_onion_links_from_csv(csv_file)

    success_count = 0
    for url in onion_links:
        result = extract_text_and_images(url)
        if result:
            save_single_result(result)
            success_count += 1
        time.sleep(10)  # politeness delay

    print(f"\n[✓] Done. {success_count}/{len(onion_links)} links processed successfully.")

# === Entry point ===
if __name__ == '__main__':
    query = input("Enter a keyword or phrase to search the dark web: ").strip()
    run_pipeline(query)
