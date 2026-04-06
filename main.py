import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import json
import os
import logging
import sys
import time
from tqdm import tqdm
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DB_FILE = "indexed_urls.txt"
HTML_SITEMAP = "index.html" 
XML_SITEMAP = "sitemap.xml" 
ROBOTS_FILE = "robots.txt"

VERIFIED_DOMAINS = ["readme.io", "webflow.io", "pages.dev", "github.io", "blogspot.com"]

# --- MASUKKAN LINK BARU DI SINI ---
MANUAL_URLS = [
    "https://marty-supreme-8k.readme.io/reference/marty-supreme",
	"https://marty-supreme-12-k-ko.readme.io/reference/marty-supreme-timothee",
	"https://marty-supreme-fhd.readme.io/reference/marty-supreme-12k",
	"https://marty-supreme-fhd-2026.readme.io/reference/marty-supreme-2026",
	"https://pavane-8.readme.io/reference/pavane-2026-8k",
	"https://pavane-uncut-12k.readme.io/reference/pavane-uncut-12k",
	"https://watch-pavane.readme.io/reference/watch-pavane-fhd",
	"https://pavane-fhd.readme.io/reference/pavane-byunyohan-full",
	"https://bloodhounds-s2.readme.io/reference/bloodhounds-s2-8k",
	"https://bloodhounds-2.readme.io/reference/bloodhounds-2-uncut-12k",
	"https://bloodhounds-s2-fhd.readme.io/reference/bloodhounds-s2-cast-full",
	"https://watch-bloodhounds-s2-fhd.readme.io/reference/watch-bloodhounds-s2-fhd",
	"https://never-forget-your-enemy-ep6-8k.readme.io/reference/never-forget-your-enemy-ep6-8k",
	"https://enemy-ep6-12k-kkodu.readme.io/reference/enemy-ep6-12k-kkodu",
	"https://never-forget-enemy-ep6-fhd.readme.io/reference/watch-never-forget-enemy-ep6-fhd",
	"https://never-forget-enemy-ep6-review.readme.io/reference/never-forget-enemy-ep6-review",
	"https://enemy-ep6-12k.readme.io/reference/bts-return-12k-official",
	"https://bts-the-return.readme.io/reference/bts-the-return-8k",
	"https://bts-return-fhd.readme.io/reference/watch-bts-return-fhd",
	"https://bts-return-full-movie.readme.io/reference/bts-return-full-movie",
]
HUB_URL = "https://zerooscreen.github.io/my-indexer/"

def generate_robots_txt():
    content = f"User-agent: *\nAllow: /\n\nSitemap: {HUB_URL}sitemap.xml"
    with open(ROBOTS_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Robots.txt Berhasil Dibuat.")

def generate_html_sitemap(urls):
    meta_verifikasi = '<meta name="google-site-verification" content="jkO82p0n2lmtm7R_TubD9cyAVSxfwpILpgn6zjD-Pvk" />'
    teks_seo = """
    <div style="margin-bottom:30px; color:#444; text-align:justify; background:#e8f0fe; padding:25px; border-radius:15px; border-left:6px solid #1a73e8;">
        <h2 style="color:#1a73e8; margin-top:0;">Global Cinema & Series Update Hub</h2>
        <p>Selamat datang di platform rujukan film internasional. Kami menyediakan daftar pembaruan untuk series Thailand Uncut dan sinema global lainnya.</p>
    </div>
    """
    header = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    {meta_verifikasi}<meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Movie Indexer Hub</title>
    <style>body{{font-family:sans-serif;background:#f0f2f5;padding:20px}}.container{{max-width:850px;margin:auto;background:white;padding:40px;border-radius:20px;box-shadow:0 15px 35px rgba(0,0,0,0.1)}}
    h1{{color:#1a73e8;text-align:center;border-bottom:4px solid #1a73e8;padding-bottom:15px}}ul{{list-style:none;padding:0}}li{{border-bottom:1px solid #eee;padding:15px 0}}a{{color:#1a73e8;text-decoration:none;font-weight:600}}</style></head>
    <body><div class="container"><h1>🎬 Movie Update Hub</h1>{teks_seo}<ul>"""
    footer = f"</ul><div style='text-align:center;margin-top:30px;font-size:0.9em;color:#777'>Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div></div></body></html>"
    list_items = ""
    for url in sorted(list(urls), reverse=True):
        if "github.io" in url: continue
        slug = url.split('/')[-1].replace('-', ' ').title()
        list_items += f'<li><a href="{url}" target="_blank">{slug}</a></li>\n'
    with open(HTML_SITEMAP, "w", encoding="utf-8") as f:
        f.write(header + list_items + footer)

def generate_xml_sitemap():
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    xml_content = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>{HUB_URL}</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n</urlset>'
    with open(XML_SITEMAP, "w", encoding="utf-8") as f:
        f.write(xml_content)

def send_to_google(urls):
    try:
        info = json.loads(os.environ['INDEXER_CONFIG'])
        creds = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
        from googleapiclient.discovery import build
        service = build('indexing', 'v3', credentials=creds)
        for url in tqdm(urls):
            service.urlNotifications().publish(body={"url": url, "type": "URL_UPDATED"}).execute()
            with open(DB_FILE, "a") as f: f.write(url + "\n")
            time.sleep(1)
    except Exception as e: logger.error(f"API Error: {e}")

def run_indexer():
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    with open(DB_FILE, "r") as f: indexed = set(line.strip() for line in f if line.strip())
    all_urls = set(MANUAL_URLS).union(indexed)
    
    generate_html_sitemap(all_urls)
    generate_xml_sitemap()
    generate_robots_txt()
    
    new_urls = [u for u in MANUAL_URLS if u not in indexed]
    api_queue = [u for u in new_urls if any(d in u for d in VERIFIED_DOMAINS)]
    if api_queue: send_to_google(api_queue)

if __name__ == "__main__":
    run_indexer()
