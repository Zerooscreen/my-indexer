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

# --- DAFTAR URL FILM (MAKSIMAL 200 URL BARU PER HARI) ---
# Tambahkan link baru Anda di bawah kategori negara masing-masing agar rapi.
MANUAL_URLS = [
    # === KOREA / THAILAND / VIETNAM ===
    "https://onepiece-season2-full-fhd-sub.readme.io/reference/onepiece-season2-full-fhd-sub",
    "https://onepiece-season2-full-fhd.readme.io/reference/onepiece-season2-full-fhd",
    "https://watch-onepiece2-korean-sub.readme.io/reference/watch-onepiece2-korean-sub",
    "https://mickey-17-full-fhd-bongjoonho.readme.io/reference/mickey-17-full-fhd-bongjoonho",
    "https://mickey-17-bong-joon-ho-fhd.readme.io/reference/mickey-17-bong-joon-ho-fhd",
    "https://watch-mickey-17-full-movie.readme.io/reference/watch-mickey-17-full-movie",
    "https://hoppers-2026-full-fhd-sub.readme.io/reference/hoppers-2026-full-fhd-sub",
    "https://hoppers-2026-fhd-sub.readme.io/reference/hoppers-2026-fhd-sub",
    "https://hoppers-pixar-full-movie.readme.io/reference/hoppers-pixar-full-movie",
    "https://scream-7-full-fhd-korean.readme.io/reference/scream-7-full-fhd-korean",
    "https://scream-7-horror-fhd.readme.io/reference/scream-7-horror-fhd",
    "https://scream-7-full-movie-sub.readme.io/reference/scream-7-full-movie-sub",

    # === FRANCE / BULGARIA ===
    # 

    # === BRAZIL ===
    # 
]

# URL Hub Indexer Anda (GitHub Pages)
HUB_URL = "https://zerooscreen.github.io/my-indexer/"
MANUAL_URLS.append(HUB_URL)

def get_already_indexed():
    """Mengambil daftar URL yang sudah sukses ter-index dari database lokal"""
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_indexed_url(url):
    """Menyimpan URL yang sukses ke database agar tidak dikirim ulang"""
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def generate_html_sitemap(urls):
    """Membuat tampilan website Hub (index.html) yang profesional dan SEO Friendly"""
    # MASUKKAN KODE VERIFIKASI GOOGLE SEARCH CONSOLE BARU DI SINI (Jika ada)
    meta_verifikasi = """
    <meta name="google-site-verification" content="jkO82p0n2lmtm7R_TubD9cyAVSxfwpILpgn6zjD-Pvk" />
    """
    
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
    
    # Sortir URL agar yang terbaru berada di atas
    for url in sorted(list(urls), reverse=True):
        if "github.io" in url: continue
        # Mengubah slug URL menjadi judul yang rapi
        slug = url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
        list_items += f'<li><a href="{url}" target="_blank">{slug}</a></li>\n'
    
    with open(HTML_SITEMAP, "w", encoding="utf-8") as f:
        f.write(header + list_items + footer)

def generate_xml_sitemap(urls):
    """Membuat sitemap.xml otomatis untuk robot Google"""
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    footer = '</urlset>'
    items = ""
    # Link utama Hub
    items += f'  <url>\n    <loc>{HUB_URL}</loc>\n    <lastmod>{now}</lastmod>\n    <priority>1.0</priority>\n  </url>\n'
    for url in urls:
        if "github.io" in url: continue
        items += f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{now}</lastmod>\n    <priority>0.8</priority>\n  </url>\n'
    with open(XML_SITEMAP, "w", encoding="utf-8") as f:
        f.write(header + items + footer)

def send_to_google(urls):
    """Mengirim URL baru ke Google Indexing API"""
    if not urls: return
    try:
        info = json.loads(os.environ['INDEXER_CONFIG'])
        credentials = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
    except Exception as e:
        logger.error(f"Error Konfigurasi: {e}")
        return

    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    for url in tqdm(urls, desc="Indexing"):
        try:
            credentials.refresh(Request())
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {credentials.token}"}
            res = requests.post(endpoint, headers=headers, json={"url": url, "type": "URL_UPDATED"})
            if res.status_code == 200:
                save_indexed_url(url)
        except Exception as e:
            logger.error(f"Gagal mengirim {url}: {e}")

def run_indexer():
    """Fungsi utama menjalankan seluruh proses"""
    all_manual = set(MANUAL_URLS)
    indexed = get_already_indexed()
    total_urls_for_sitemap = all_manual.union(indexed)
    
    # Update Website Hub & Sitemap
    generate_html_sitemap(total_urls_for_sitemap)
    generate_xml_sitemap(total_urls_for_sitemap)
    
    # Filter hanya link yang benar-benar baru (belum ada di indexed_urls.txt)
    new_urls = [u for u in MANUAL_URLS if u not in indexed]
    
    if new_urls:
        logger.info(f"Ditemukan {len(new_urls)} link baru. Mengirim ke Google...")
        send_to_google(new_urls)
    else:
        logger.info("Semua URL sudah ter-index sebelumnya. Melewati pengiriman.")
    
    logger.info("--- PROSES SELESAI ---")

if __name__ == "__main__":
    run_indexer()
