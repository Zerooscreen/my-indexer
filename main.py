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

# --- DAFTAR URL --- (Silakan ganti dengan link film baru Anda)
MANUAL_URLS = [
    "https://dead-echoes-fhd.readme.io/reference/dead-echoes-fhd",
]

HUB_URL = "https://zerooscreen.github.io/my-indexer/"

def generate_robots_txt():
    """Membuat robots.txt resmi"""
    content = f"User-agent: *\nAllow: /\n\nSitemap: {HUB_URL}sitemap.xml"
    with open(ROBOTS_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def generate_html_sitemap(urls):
    meta_verifikasi = '<meta name="google-site-verification" content="jkO82p0n2lmtm7R_TubD9cyAVSxfwpILpgn6zjD-Pvk" />'
    teks_seo = """
    <div style="margin-bottom:30px; color:#444; text-align:justify; background:#e8f0fe; padding:25px; border-radius:15px; border-left:6px solid #1a73e8;">
        <h2 style="color:#1a73e8; margin-top:0;">Global Cinema & Series Hub</h2>
        <p>Welcome to our movie indexing hub. We provide latest updates for Thai Uncut series and international cinema.</p>
    </div>
    """
    header = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    {meta_verifikasi}<meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Movie Indexer Hub</title>
    <style>body{{font-family:sans-serif;background:#f0f2f5;padding:20px}}.container{{max-width:800px;margin:auto;background:white;padding:30px;border-radius:15px;box-shadow:0 5px 15px rgba(0,0,0,0.05)}}
    h1{{color:#1a73e8;text-align:center}}ul{{list-style:none;padding:0}}li{{border-bottom:1px solid #eee;padding:10px 0}}a{{color:#1a73e8;text-decoration:none;font-weight:600}}</style></head>
    <body><div class="container"><h1>🎬 Movie Update Hub</h1>{teks_seo}<ul>"""
    footer = f"</ul><div style='text-align:center;margin-top:20px;font-size:0.8em;color:#999'>Last Update: {datetime.now().strftime('%Y-%m-%d')}</div></div></body></html>"
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
    all_urls = set(MANUAL_URLS)
    total_urls = all_urls.union(indexed)
    
    # Generate 3 file inti
    generate_html_sitemap(total_urls)
    generate_xml_sitemap()
    generate_robots_txt()
    
    new_urls = [u for u in MANUAL_URLS if u not in indexed]
    api_queue = [u for u in new_urls if any(d in u for d in VERIFIED_DOMAINS)]
    if api_queue: send_to_google(api_queue)

if __name__ == "__main__":
    run_indexer()
