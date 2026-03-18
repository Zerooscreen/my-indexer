import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import json
import os
import logging
import sys
import time # PENTING: Untuk jeda waktu
from tqdm import tqdm
from datetime import datetime

# --- 1. KONFIGURASI LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DB_FILE = "indexed_urls.txt"
HTML_SITEMAP = "index.html" 
XML_SITEMAP = "sitemap.xml" 

# --- 2. DAFTAR URL FILM (MAKSIMAL 200 URL BARU PER HARI) ---
MANUAL_URLS = [
    # === KOREA / THAILAND / VIETNAM ===
    "https://onepiece2-ep1-8-fhd.readme.io/reference/onepiece2-ep1-8",
	"https://op2-live-action.readme.io/reference/op2-live-action",
	"https://op2-netflix.readme.io/reference/op2-netflix",
	"https://op2-fhd-full.readme.io/reference/op2-fhd-full",
	"https://op2-thai-fullhd.readme.io/reference/watch-onepiece2",
	"https://op2-thai-full-hd.readme.io/reference/op2-thai-full",
	"https://ghostboard-fhd-2026.readme.io/reference/ghostboard-fhd",
	"https://ghostboard-2026.readme.io/reference/watch-ghostboard",
	"https://ghostboard-master.readme.io/reference/ghostboard-master",
	"https://ghostboard-sub-thai.readme.io/reference/ghostboard-thai",
	"https://ghostboard-uhd-2026.readme.io/reference/ghostboard-2026",
	"https://ghostboard-online.readme.io/reference/ghostboard-onlin",
	
    # === FRANCE / BULGARIA ===
    # 
    

    # === BRAZIL ===
    # 
    
]

# URL Hub Indexer Anda (Harus konsisten dengan GSC)
HUB_URL = "https://zerooscreen.github.io/my-indexer/"

# --- 3. FUNGSI DATABASE & SITEMAP GENERATOR ---

def get_already_indexed():
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_indexed_url(url):
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def generate_html_sitemap(urls):
    """Membuat website Hub index.html (Backlink Power)"""
    meta_verifikasi = '<meta name="google-site-verification" content="jkO82p0n2lmtm7R_TubD9cyAVSxfwpILpgn6zjD-Pvk" />'
    header = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    {meta_verifikasi}
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Movie Indexer Hub</title>
    <style>
        body{{font-family:'Segoe UI',Tahoma,Arial,sans-serif;background:#f4f7f9;padding:20px;color:#333;line-height:1.6}}
        .container{{max-width:800px;margin:auto;background:white;padding:30px;border-radius:15px;box-shadow:0 10px 25px rgba(0,0,0,0.05)}}
        h1{{color:#1a73e8;text-align:center;border-bottom:3px solid #1a73e8;padding-bottom:15px;margin-bottom:20px}}
        ul{{list-style:none;padding:0}}
        li{{border-bottom:1px solid #f0f0f0;padding:12px 0;transition:all 0.2s}}
        li:hover{{background:#fafafa;padding-left:10px}}
        a{{color:#1a73e8;text-decoration:none;font-weight:600;font-size:1.05em;display:block}}
        a:hover{{color:#d93025}}
        .footer{{text-align:center;margin-top:25px;font-size:0.85em;color:#999;border-top:1px solid #eee;padding-top:15px}}
    </style></head>
    <body><div class="container"><h1>🎬 Global Movie Update</h1><ul>"""
    
    footer = f"</ul><div class='footer'>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC</div></div></body></html>"
    list_items = ""
    for url in sorted(list(urls), reverse=True):
        if "github.io" in url: continue
        slug = url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
        list_items += f'<li><a href="{url}" target="_blank">{slug}</a></li>\n'
    
    with open(HTML_SITEMAP, "w", encoding="utf-8") as f:
        f.write(header + list_items + footer)

def generate_xml_sitemap():
    """Hanya isi Link Hub agar GSC berstatus HIJAU (Validasi Domain)"""
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{HUB_URL}</loc>
    <lastmod>{now}</lastmod>
    <priority>1.0</priority>
  </url>
</urlset>"""
    with open(XML_SITEMAP, "w", encoding="utf-8") as f:
        f.write(xml_content)
    logger.info("Sitemap XML diperbarui (GSC Validation Mode).")

# --- 4. FUNGSI PENGIRIMAN KE GOOGLE ---

def send_to_google(urls):
    if not urls: return
    try:
        info = json.loads(os.environ['INDEXER_CONFIG'])
        credentials = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
    except: return

    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    for url in tqdm(urls, desc="Indexing"):
        try:
            credentials.refresh(Request())
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {credentials.token}"}
            res = requests.post(endpoint, headers=headers, json={"url": url, "type": "URL_UPDATED"})
            if res.status_code == 200:
                save_indexed_url(url)
            
            # --- PENGATURAN WAKTU (DELAY) ---
            # Jeda 1 detik antar URL agar stabil dan tidak menggantung
            time.sleep(1) 
            
        except Exception as e:
            logger.error(f"Gagal mengirim {url}: {e}")

def run_indexer():
    # Salin list manual dan tambahkan Hub
    temp_manual = MANUAL_URLS.copy()
    if HUB_URL not in temp_manual:
        temp_manual.append(HUB_URL)
        
    all_manual = set(temp_manual)
    indexed = get_already_indexed()
    total_urls_for_html = all_manual.union(indexed)
    
    # 1. Update Website Hub (Lengkap untuk SEO)
    generate_html_sitemap(total_urls_for_html)
    
    # 2. Update XML (Link Hub saja agar GSC Hijau)
    generate_xml_sitemap()
    
    # 3. Filter Link Baru
    new_urls = [u for u in temp_manual if u not in indexed]
    
    if new_urls:
        logger.info(f"Ditemukan {len(new_urls)} link baru. Mengirim ke Google...")
        send_to_google(new_urls)
    else:
        logger.info("Semua URL sudah ter-index. Melewati pengiriman API.")
    
    logger.info("--- PROSES SELESAI ---")

if __name__ == "__main__":
    run_indexer()
