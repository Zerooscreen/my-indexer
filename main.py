import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import json
import os
import logging
import sys
from tqdm import tqdm

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DB_FILE = "indexed_urls.txt"
HTML_SITEMAP = "backlinks.html" 

# --- DAFTAR URL MANUAL ---
MANUAL_URLS = [
    "https://the-earth-ep6.readme.io/reference/วิวาห์ปฐพี-the-earth-ep6-พากย์ไทย-uncut",
    "https://the-earth-ep6.readme.io/reference/the-earth-ep6-thai-series-uncut",
    "https://be-my-angel-ep5.readme.io/reference/ฉันหลงรักเทวดาของฉัน-ep5-ดูฟรี-uncut",
    "https://be-my-angel-ep5.readme.io/reference/be-my-angel-ep5-thai-dub-hd",
    "https://heart-code-ep5.readme.io/reference/heart-code-สืบลับจับใจ-ep5-uncut",
    "https://heart-code-ep5.readme.io/reference/สืบลับจับใจ-ep5-thai-sub-2026",
    "https://i-wanna-be-suptar-ep4.readme.io/reference/วันหนึ่งจะเป็นซุปตาร์-ep4-ดูฟรี-hd",
    "https://i-wanna-be-suptar-ep4.readme.io/reference/i-wanna-be-suptar-ep4-thai-series",
    "https://play-park-the-series-ep2.readme.io/reference/รักไม่คาดฝัน-play-park-ep2-uncut",
    "https://play-park-the-series-ep2.readme.io/reference/play-park-the-series-ep2-thai-uncut",
    "https://frozen-valentine-ep3.readme.io/reference/ปิ๊งรักคุณพี่เย็นชา-ep3-ดูฟรี-uncut",
    "https://frozen-valentine-ep3.readme.io/reference/frozen-valentine-ep3-thai-series-uncut",
]

def get_already_indexed():
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_indexed_url(url):
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def generate_backlink_page(urls):
    """Membuat halaman HTML hub backlink"""
    header = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Sitemap Movie Hub</title>
    <style>body{font-family:sans-serif;background:#f9f9f9;padding:20px} .box{max-width:700px;margin:auto;background:white;padding:20px;border-radius:10px;box-shadow:0 2px 5px rgba(0,0,0,0.1)}
    a{color:#007bff;text-decoration:none;font-weight:bold} li{margin-bottom:10px;border-bottom:1px solid #eee;padding-bottom:5px}</style></head>
    <body><div class="box"><h1>Movie Backlink Hub</h1><ul>"""
    footer = "</ul></div></body></html>"
    list_items = ""
    for url in sorted(list(urls), reverse=True):
        slug = url.split('/')[-1].replace('-', ' ').title()
        list_items += f'<li><a href="{url}">{slug}</a></li>\n'
    with open(HTML_SITEMAP, "w", encoding="utf-8") as f:
        f.write(header + list_items + footer)

def send_to_google(urls):
    if not urls: return
    try:
        info = json.loads(os.environ['INDEXER_CONFIG'])
        credentials = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
    except: return
    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    for url in tqdm(urls):
        try:
            credentials.refresh(Request())
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {credentials.token}"}
            res = requests.post(endpoint, headers=headers, json={"url": url, "type": "URL_UPDATED"})
            if res.status_code == 200: save_indexed_url(url)
        except: pass

def run_indexer():
    all_manual = set(MANUAL_URLS)
    indexed = get_already_indexed()
    # Update HTML Sitemap dengan semua link yang pernah ada
    generate_backlink_page(all_manual.union(indexed))
    # Kirim hanya link baru ke Google
    new_urls = [u for u in MANUAL_URLS if u not in indexed]
    if new_urls:
        logger.info(f"Mengirim {len(new_urls)} URL ke Google...")
        send_to_google(new_urls)
    logger.info("Proses selesai.")

if __name__ == "__main__":
    run_indexer()
