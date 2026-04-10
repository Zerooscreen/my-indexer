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

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DB_FILE = "indexed_urls.txt"
HTML_SITEMAP = "index.html" 
XML_SITEMAP = "sitemap.xml" 
ROBOTS_FILE = "robots.txt"

# --- DOMAIN VERIFIED GSC ---
VERIFIED_DOMAINS = ["readme.io", "webflow.io", "pages.dev", "github.io", "blogspot.com"]

# --- DAFTAR URL FILM ---
MANUAL_URLS = [
    "https://shock-me-girls-ep9.readme.io/reference/ep10",
	"https://shock-me-girls-ep9-uncut.readme.io/reference/shock-me-girls-ep10-uncut",
	"https://shockmegirls-ep9.readme.io/reference/ep-10",
	"https://shockmegirls-ep-9.readme.io/reference/shock-me-girls-ep10",
	"https://shadow-of-love-ep-4.readme.io/reference/ep10",
	"https://shadow-of-love-ep4-uncut.readme.io/reference/shadow-of-love-ep10-uncut",
	"https://shadowoflove-ep4.readme.io/reference/shadow-of-love-ep10",
	"https://shadow-of-love-ep-4-uncut.readme.io/reference/ep10",
	"https://frozen-valentine-ep-9.readme.io/reference/ep10",
	"https://frozen-valentine-ep9.readme.io/reference/frozen-valentine-ep10",
	"https://frozenvalentine-ep9.readme.io/reference/frozen-valentine-ep10-uncut",
	"https://broken-of-love-ep-2.readme.io/reference/ep3",
	"https://broken-of-love-ep2.readme.io/reference/broken-of-love-ep3",
	"https://brokenofloveep2.readme.io/reference/ep-3",
	"https://broken-of-love-ep2-uncut.readme.io/reference/ep3",
]

HUB_URL = "https://zerooscreen.github.io/my-indexer/"

def generate_robots_txt():
    content = "User-agent: *\nAllow: /\n\nSitemap: " + HUB_URL + "sitemap.xml"
    with open(ROBOTS_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def generate_html_sitemap(urls):
    """Website Hub Pro dengan Schema Markup"""
    meta_verif = '<meta name="google-site-verification" content="jkO82p0n2lmtm7R_TubD9cyAVSxfwpILpgn6zjD-Pvk" />'
    
    # CSS & HTML Template
    style = """
    <style>
        :root { --p: #1a73e8; --a: #d93025; --b: #f8f9fa; }
        body { font-family: sans-serif; background: var(--b); margin: 0; padding: 20px; color: #333; }
        .con { max-width: 900px; margin: auto; }
        .hero { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 5px 20px rgba(0,0,0,0.05); text-align: center; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; }
        .card { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); position: relative; border: 1px solid #eee; }
        .card:hover { border-color: var(--p); transform: translateY(-3px); transition: 0.2s; }
        .card-t { font-weight: bold; color: var(--p); text-decoration: none; display: block; margin-bottom: 5px; }
        .badge { background: var(--a); color: white; font-size: 10px; padding: 2px 6px; border-radius: 4px; float: right; }
    </style>
    """
    
    schema_items = []
    list_cards = ""
    
    for url in sorted(list(urls), reverse=True):
        if "github.io" in url: continue
        slug = url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
        if not slug or len(slug) < 3: slug = url
        
        list_cards += f'<div class="card"><span class="badge">HD</span><a class="card-t" href="{url}" target="_blank">{slug}</a><small style="color:#999">Global Series Update</small></div>\n'
        schema_items.append({"@type": "ListItem", "position": len(schema_items)+1, "url": url, "name": slug})

    schema_json = json.dumps({"@context": "https://schema.org", "@type": "ItemList", "itemListElement": schema_items})
    
    html_content = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">{meta_verif}
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Movie Indexer Hub</title>{style}
    <script type="application/ld+json">{schema_json}</script></head>
    <body><div class="con"><div class="hero"><h1>🎬 Movie Update Hub</h1><p>Premium reference for Thai Uncut & International Series.</p></div>
    <div class="grid">{list_cards}</div>
    <div style="text-align:center;margin-top:30px;color:#999"><small>Last Sync: {datetime.now().strftime('%Y-%m-%d')}</small></div></div></body></html>"""
    
    with open(HTML_SITEMAP, "w", encoding="utf-8") as f:
        f.write(html_content)

def generate_xml_sitemap():
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>{HUB_URL}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod><priority>1.0</priority></url>\n</urlset>'
    with open(XML_SITEMAP, "w", encoding="utf-8") as f:
        f.write(xml)

def send_to_google(urls):
    try:
        info = json.loads(os.environ['INDEXER_CONFIG'])
        creds = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
        from googleapiclient.discovery import build
        service = build('indexing', 'v3', credentials=creds)
        for url in tqdm(urls):
            try:
                service.urlNotifications().publish(body={"url": url, "type": "URL_UPDATED"}).execute()
                with open(DB_FILE, "a") as f: f.write(url + "\n")
                time.sleep(1)
            except: continue
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
    
    if api_queue:
        logger.info(f"Mengirim {len(api_queue)} link ke API...")
        send_to_google(api_queue)
    
    # Save non-verified to DB so they don't loop
    for u in new_urls:
        if not any(d in u for d in VERIFIED_DOMAINS):
            with open(DB_FILE, "a") as f: f.write(u + "\n")

if __name__ == "__main__":
    run_indexer()
