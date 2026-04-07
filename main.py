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

# --- 1. KONFIGURASI LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DB_FILE = "indexed_urls.txt"
HTML_SITEMAP = "index.html" 
XML_SITEMAP = "sitemap.xml" 
ROBOTS_FILE = "robots.txt"

# --- 2. DAFTAR DOMAIN VERIFIED GSC (BISA KIRIM API) ---
VERIFIED_DOMAINS = ["readme.io", "webflow.io", "pages.dev", "github.io", "blogspot.com"]

# --- 3. DAFTAR URL FILM HARI INI ---
MANUAL_URLS = [
    # Tempel Link Baru Anda di Sini:
    "https://zyo.se/devoradores-de-estrelas",
	"https://zyo.se/sevoradores-de-estrelas-2026",
]

# URL Hub Indexer Anda
HUB_URL = "https://zerooscreen.github.io/my-indexer/"

# --- 4. FUNGSI GENERATOR ---

def generate_robots_txt():
    content = f"User-agent: *\nAllow: /\n\nSitemap: {HUB_URL}sitemap.xml"
    with open(ROBOTS_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def generate_html_sitemap(urls):
    """Membuat Website Hub Kelas Profesional dengan Movie Schema untuk Ranking"""
    meta_verifikasi = '<meta name="google-site-verification" content="jkO82p0n2lmtm7R_TubD9cyAVSxfwpILpgn6zjD-Pvk" />'
    
    # Header dengan CSS Modern (Card Layout)
    header = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    {meta_verifikasi}
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Cinema Hub - Premium Thai Uncut & World Series</title>
    <style>
        :root {{ --primary: #1a73e8; --accent: #d93025; --bg: #f8f9fa; }}
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); margin: 0; padding: 20px; color: #333; }}
        .container {{ max-width: 900px; margin: auto; }}
        .hero {{ background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); text-align: center; margin-bottom: 30px; }}
        h1 {{ color: var(--primary); font-size: 2.5em; margin-bottom: 10px; }}
        .intro {{ color: #666; font-size: 1.1em; line-height: 1.6; max-width: 700px; margin: auto; text-align: justify; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-top: 30px; }}
        .card {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.03); transition: 0.3s; border: 1px solid #eee; position: relative; overflow: hidden; }}
        .card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); border-color: var(--primary); }}
        .badge {{ position: absolute; top: 10px; right: 10px; background: var(--accent); color: white; font-size: 0.7em; padding: 4px 8px; border-radius: 5px; font-weight: bold; }}
        .card-title {{ font-weight: bold; color: var(--primary); font-size: 1.1em; margin-bottom: 10px; display: block; text-decoration: none; }}
        .card-meta {{ font-size: 0.85em; color: #888; }}
        .footer {{ text-align: center; margin-top: 50px; padding: 20px; color: #999; border-top: 1px solid #eee; }}
    </style>
    """
    
    # --- MEMBUAT SCHEMA MARKUP ---
    schema_items = []
    list_cards = ""
    
    for url in sorted(list(urls), reverse=True):
        if "github.io" in url: continue
        
        # Ekstrak Judul
        slug = url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
        if not slug or len(slug) < 3: slug = url
        
        # Buat HTML Card
        list_cards += f"""
        <div class="card">
            <span class="badge">NEW HD</span>
            <a class="card-title" href="{url}" target="_blank">{slug}</a>
            <div class="card-meta">Category: International Series<br>Format: Uncut / Full Version</div>
        </div>
        """
        
        # Tambah ke Schema list
        schema_items.append({
            "@type": "ListItem",
            "position": len(schema_items) + 1,
            "url": url,
            "name": slug
        })

    # Gabungkan Schema JSON-LD
    schema_json = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": schema_items
    }
    
    full_html = f"""
    {header}
    <script type="application/ld+json">{json.dumps(schema_json)}</script>
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <h1>🎬 Global Movie Update Hub</h1>
                <div class="intro">
                    Welcome to the most comprehensive digital library for international cinema enthusiasts. 
                    We provide curated links for the latest Thai Uncut series, Korean dramas, and exclusive 
                    releases from Brazil and France. Our automated system ensures that you receive the most 
                    up-to-date and verified reference links available on the web today.
                </div>
            </div>
            
            <div class="grid">
                {list_cards}
            </div>
            
            <div class="footer">
                &copy; {datetime.now().year} Global Movie Hub Indexer. All links verified. <br>
                Last Sync: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(HTML_SITEMAP, "w", encoding="utf-8") as f:
        f.write(full_html)

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
    with open(DB_FILE, "r", encoding="utf-8") as f: indexed = set(line.strip() for line in f if line.strip())
    
    all_manual = set(MANUAL_URLS).union(indexed)
    
    # 1. Generate All Files (HTML Hub, Sitemap, Robots)
    generate_html_sitemap(all_manual)
    generate_xml_sitemap()
    generate_robots_txt()
    
    # 2. API Indexing Logic
    new_urls = [u for u in MANUAL_URLS if u not in indexed]
    api_queue = [u for u in new_urls if any(d in u for d in VERIFIED_DOMAINS)]
    
    if api_queue:
        logger.info(f"Mengirim {len(api_queue)} link terverifikasi ke API...")
        send_to_google(api_queue)
    
    # Jika ada link non-verif, simpan ke database agar tidak diulang
    for u in new_urls:
        if not any(d in u for d in VERIFIED_DOMAINS):
            save_indexed_url(u)

if __name__ == "__main__":
    run_indexer()
