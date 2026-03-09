import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import json
import os
import logging
import sys
from tqdm import tqdm
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DB_FILE = "indexed_urls.txt"
HTML_SITEMAP = "index.html" 
XML_SITEMAP = "sitemap.xml" 

# --- DAFTAR URL FILM ---
MANUAL_URLS = [
    "https://onepiece-s2-skull-full.readme.io/reference/onepiece-s2-skull-full",
	"https://op2-straw-hat-thai.readme.io/reference/op2-straw-hat-thai",
	"https://onepiece2-pirate-flag.readme.io/reference/onepiece2-pirate-flag",
	"https://watch-op2-skull-uhd.readme.io/reference/watch-op2-skull-uhd",
	"https://op2-ghost-pirate-full.readme.io/reference/op2-ghost-pirate-full",
	"https://onepiece2-netflix-full.readme.io/reference/onepiece2-netflix-full",
	"https://watch-onepiece2-skull.readme.io/reference/watch-onepiece2-skull",
	"https://op2-ep1-8-complete.readme.io/reference/op2-ep1-8-complete",
]
HUB_URL = "https://zerooscreen.github.io/my-indexer/"
MANUAL_URLS.append(HUB_URL)

def get_already_indexed():
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_indexed_url(url):
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def generate_html_sitemap(urls):
    """Membuat tampilan website index.html dengan KODE VERIFIKASI"""
    # MASUKKAN KODE VERIFIKASI ANDA DI SINI (DI DALAM HEADER)
    header = """<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
    <meta name="google-site-verification" content="jkO82p0n2lmtm7R_TubD9cyAVSxfwpILpgn6zjD-Pvk" />
    <title>Movie Sitemap Hub</title>
    <style>body{font-family:sans-serif;background:#f0f2f5;padding:20px}.container{max-width:700px;margin:auto;background:white;padding:20px;border-radius:12px;box-shadow:0 4px 10px rgba(0,0,0,0.1)}
    h1{color:#1a73e8;text-align:center;border-bottom:2px solid #1a73e8;padding-bottom:10px}ul{list-style:none;padding:0}li{border-bottom:1px solid #eee;padding:12px 0}
    a{color:#1a73e8;text-decoration:none;font-weight:bold;font-size:1.1em}a:hover{color:#d93025}</style></head>
    <body><div class="container"><h1>Movie Hub Update</h1><ul>"""
    
    footer = "</ul></div></body></html>"
    list_items = ""
    for url in sorted(list(urls), reverse=True):
        if "github.io" in url: continue
        slug = url.split('/')[-1].replace('-', ' ').title()
        list_items += f'<li><a href="{url}" target="_blank">{slug}</a></li>\n'
    with open(HTML_SITEMAP, "w", encoding="utf-8") as f:
        f.write(header + list_items + footer)

def generate_xml_sitemap(urls):
    """Membuat sitemap.xml otomatis"""
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    footer = '</urlset>'
    items = ""
    items += f'  <url>\n    <loc>{HUB_URL}</loc>\n    <lastmod>{now}</lastmod>\n    <priority>1.0</priority>\n  </url>\n'
    for url in urls:
        if "github.io" in url: continue
        items += f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{now}</lastmod>\n    <priority>0.8</priority>\n  </url>\n'
    with open(XML_SITEMAP, "w", encoding="utf-8") as f:
        f.write(header + items + footer)

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
    total_urls = all_manual.union(indexed)
    
    generate_html_sitemap(total_urls)
    generate_xml_sitemap(total_urls)
    
    new_urls = [u for u in MANUAL_URLS if u not in indexed]
    if new_urls:
        logger.info(f"Mengirim {len(new_urls)} link ke Google...")
        send_to_google(new_urls)
    logger.info("Proses selesai.")

if __name__ == "__main__":
    run_indexer()
