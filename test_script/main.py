import subprocess
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os

# Setup Tor proxy session
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
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if '.onion' in row['url']:
                links.append(row['url'])
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

def save_results_to_file(results, keywords):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"darkweb_results_{timestamp}.txt"
    os.makedirs("output", exist_ok=True)
    filepath = os.path.join("output", fname)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Crawl Timestamp: {timestamp}\n")
        f.write(f"Keywords: {keywords}\n")
        f.write(f"Results Found: {len(results)}\n\n")
        for entry in results:
            f.write(f"URL: {entry['url']}\n")
            f.write(f"Text Preview:\n{entry['text']}\n")
            f.write(f"Images: {', '.join(entry['images'])}\n")
            f.write("-" * 50 + "\n")

    print(f"\n[✓] Results saved to {filepath}")

def run_pipeline(query):
    csv_file = run_onionsearch(query)
    onion_links = extract_onion_links_from_csv(csv_file)

    results = []
    for url in onion_links:
        data = extract_text_and_images(url)
        if data:
            results.append(data)
        time.sleep(10)  # politeness

    save_results_to_file(results, query)

# === Entry Point ===
if __name__ == '__main__':
    query = input("Enter a keyword or phrase to search the dark web: ").strip()
    run_pipeline(query)
