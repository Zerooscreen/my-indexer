import requests
from google.oauth2 import service_account
import json
import os
import logging
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

# --- DOMAIN VERIFIED GSC (Sangat Penting: Masukkan railway.app) ---
VERIFIED_DOMAINS = ["railway.app", "github.io", "mintlify.app","lovable.app", "vercel.app", "blogspot.com"]

# --- DAFTAR URL SITUS ANDA (Update di sini jika ada film baru) ---
MANUAL_URLS = [
    "https://toy-story-5-deutsch.up.railway.app/",
	"https://toy-story-5-deutsch.up.railway.app/movie/1084244-toy-story-5-ganzer-film/",
	"https://evil-dead-burn-deutsch.up.railway.app/",
	"https://evil-dead-burn-deutsch.up.railway.app/movie/1212763-evil-dead-burn-ganzer-film/",
	"https://spiderman-4-stream-deutsch.up.railway.app/",
	"https://spiderman-4-stream-deutsch.up.railway.app/movie/969681-spider-man-brand-new-day-2026-ganzer-film-deutsch-stream/",
	"https://spiderman-2026-stream-deutsch.up.railway.app/",
	"https://spiderman-2026-stream-deutsch.up.railway.app/movie/969681-spider-man-brand-new-day-2026-ganzer-film/",
	"https://supergirl-stream-deutsch.up.railway.app/",
	"https://supergirl-stream-deutsch.up.railway.app/movie/1081003-supergirl-stream-deutsch/",
	"https://moana-stream-deutsch.up.railway.app/",
	"https://moana-stream-deutsch.up.railway.app/movie/1108427-moana-stream-deutsch/",
	"https://siamreel.up.railway.app/",
	"https://toy-story-5-deutsch.up.railway/",
	"https://evil-dead-burn-koreansub.up.railway.app/",
	"https://evil-dead-burn-koreansub.up.railway.app/movie/1212763-evil-dead-burn-koreansub/",
	"https://spiderman-2026-korean.up.railway.app/",
	"https://spiderman-2026-korean.up.railway.app/movie/969681-spider-man-brand-new-day-korean/",
	"https://odyssey-2026-koreansub.up.railway.app/",
	"https://odyssey-2026-koreansub.up.railway.app/movie/1368337-odyssey-2026-koreansub/",
	"https://spider-man-brand-new-day-thaisub.up.railway.app/",
	"https://evil-dead-burn-thaisub.up.railway.app/",
	"https://evil-dead-burn-thaisub.up.railway.app/movie/1212763-evil-dead-burn/",
	"https://sos-save-ou-rstudents.up.railway.app/",
	"https://sos-save-ou-rstudents.up.railway.app/movie/1714910-sos-save-our-students/",
	"https://spiderman-4-thaisub.up.railway.app/",
	"https://spiderman-4-thaisub.up.railway.app/movie/969681-spider-man-brand-new-day-thaisub/",
	"https://evil-dead-burn-sub-indo.up.railway.app/",
	"https://evil-dead-burn-sub-indo.up.railway.app/movie/1212763-evil-dead-burn/",
	"https://spiderman-2026-subindo-production.up.railway.app/",
	"https://spiderman-2026-subindo-production.up.railway.app/movie/969681-spider-man-brand-new-day/",
	"https://odyssey-2026-koreansub.lovable.app/",
	"https://odyssey-2026-koreansub.lovable.app/movie/1368337-odyssey-2026-koreansub/",
	"https://cinebox.up.railway.app/",
	"https://cinebox-th.up.railway.app/",
	"https://cinebox-de.up.railway.app/",
	"https://hallyuflix.up.railway.app/",
]

HUB_URL = "https://zerooscreen.github.io/my-indexer/"

def generate_robots_txt():
    content = f"User-agent: *\nAllow: /\n\nSitemap: {HUB_URL}sitemap.xml"
    with open(ROBOTS_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def generate_html_sitemap(urls):
    meta_verif = '<meta name="google-site-verification" content="jkO82p0n2lmtm7R_TubD9cyAVSxfwpILpgn6zjD-Pvk" />'
    style = "<style>:root { --p: #1a73e8; --a: #d93025; --b: #f8f9fa; } body { font-family: sans-serif; background: var(--b); padding: 20px; } .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; } .card { background: white; padding: 15px; border-radius: 12px; border: 1px solid #eee; text-align: center; } a { color: var(--p); text-decoration: none; font-weight: bold; }</style>"
    list_cards = "".join([f'<div class="card"><a href="{u}" target="_blank">{u.split("/")[-1] or "Home"}</a></div>' for u in urls if "github.io" not in u])
    html = f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'>{meta_verif}<title>Movie Hub</title>{style}</head><body><h1>🎬 Movie Indexer</h1><div class='grid'>{list_cards}</div></body></html>"
    with open(HTML_SITEMAP, "w", encoding="utf-8") as f: f.write(html)

def generate_xml_sitemap(urls):
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls: xml += f"  <url><loc>{url}</loc><lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod></url>\n"
    xml += "</urlset>"
    with open(XML_SITEMAP, "w", encoding="utf-8") as f: f.write(xml)

def send_to_google(urls):
    try:
        # Load kunci JSON dari Secret GitHub
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
    
    generate_html_sitemap(set(MANUAL_URLS).union(indexed))
    generate_xml_sitemap(set(MANUAL_URLS).union(indexed))
    generate_robots_txt()
    
    # Hanya kirim link yang belum pernah dikirim
    queue = [u for u in MANUAL_URLS if u not in indexed and any(d in u for d in VERIFIED_DOMAINS)]
    if queue:
        logger.info(f"Mengirim {len(queue)} link baru...")
        send_to_google(queue)
    else:
        logger.info("Semua link sudah terindeks sebelumnya.")

if __name__ == "__main__":
    run_indexer()
