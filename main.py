import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import json
import os
import logging
import sys
from tqdm import tqdm

# --- 1. KONFIGURASI LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# File database untuk menyimpan URL yang sudah sukses (Penting untuk GitHub Actions)
DB_FILE = "indexed_urls.txt"

# --- 2. DAFTAR URL MANUAL (Hanya masukkan link di sini) ---
MANUAL_URLS = [
    "https://scream-7-bgsub.readme.io/reference/gledai-pisyak-7-2026-tseliyat-film-online-bg-audio",
	"https://scream-7-bgsub.readme.io/reference/pisyak-7-2026-online-bg-sub-audio",
	"https://goat-bg-sub.readme.io/reference/gledai-shampion-po-priroda-goat-online-bg-audio",
	"https://goat-bg-sub.readme.io/reference/goat-film-2026-online-bg-sub-audio",
	"https://crime-101-bgsub.readme.io/reference/gledai-prestaplenie-101-crime-101-online-bg-audio",
	"https://crime-101-bgsub.readme.io/reference/crime-101-online-bg-sub-audio",
	"https://the-strangers-chapter-3-bg-sub.readme.io/reference/gledai-bezlikite-glava-3-the-strangers-chapter-3-online-bg-audio",
	"https://the-strangers-chapter-3-bg-sub.readme.io/reference/bezlikite-3-2026-online-bg-sub-audio",
	"https://wuthering-heights-bg-sub.readme.io/reference/gledai-bruleni-halmove-wuthering-heights-online-bg-audio",
	"https://wuthering-heights-bg-sub.readme.io/reference/bruleni-halmove-2026-online-bg-sub-audio",
	"https://return-to-silent-hill-bg-sub.readme.io/reference/gledai-zavrashtane-v-saylant-hil-return-to-silent-hill-online-bg-audio",
	"https://return-to-silent-hill-bg-sub.readme.io/reference/return-to-silent-hill-2026-online-bg-sub-audio",
	"https://greenland-migration-bg-sub.readme.io/reference/gledai-grenlandiya-2-migratsiya-2026-online-bg-audio",
	"https://greenland-migration-bg-sub.readme.io/reference/greenland-2-migration-2026-online-bg-sub-audio",
	"https://28-years-later-bg-sub.readme.io/reference/gledai-28-godini-po-kasno-2-hram-ot-kosti-online-bg-audio",
	"https://28-years-later-bg-sub.readme.io/reference/28-years-later-2-2026-online-bg-sub-audio",
	"https://mercy-full-movie-bg-sub.readme.io/reference/gledai-90-minuti-do-prisada-mercy-online-bg-audio",
	"https://mercy-full-movie-bg-sub.readme.io/reference/mercy-2026-online-bg-sub-audio",
]

# --- 3. FUNGSI CEK DATABASE (Agar tidak double index) ---

def get_already_indexed():
    """Membaca list URL yang sudah pernah sukses di-index sebelumnya"""
    if not os.path.exists(DB_FILE):
        return set()
    with open(DB_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_indexed_url(url):
    """Menambah URL ke database setelah berhasil dikirim ke Google"""
    with open(DB_FILE, "a") as f:
        f.write(url + "\n")

# --- 4. FUNGSI PENGIRIMAN KE GOOGLE INDEXING API ---

def send_to_google(urls):
    if not urls:
        return

    try:
        # Mengambil file JSON Kredensial dari GitHub Secrets
        info = json.loads(os.environ['INDEXER_CONFIG'])
        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/indexing"]
        )
        logger.info("Kredensial Google Cloud berhasil dimuat.")
    except Exception as e:
        logger.error(f"Gagal memuat kredensial: {e}")
        return

    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    
    for url in tqdm(urls, desc="Proses Indexing", unit="url"):
        try:
            credentials.refresh(Request())
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {credentials.token}"
            }
            data = {"url": url, "type": "URL_UPDATED"}
            res = requests.post(endpoint, headers=headers, json=data)
            
            if res.status_code == 200:
                # Berhasil! Simpan link ke file database
                save_indexed_url(url)
            else:
                tqdm.write(f"Gagal [{res.status_code}] : {url} | Pesan: {res.text}")
                
        except Exception as e:
            tqdm.write(f"Error pada {url}: {e}")

# --- 5. EKSEKUSI UTAMA ---

def run_indexer():
    # 1. Ambil semua link dari daftar manual di atas
    all_urls = list(set(MANUAL_URLS))

    # 2. Ambil data link yang sudah pernah di-index
    already_indexed = get_already_indexed()

    # 3. Filter: Hanya ambil link yang belum ada di database
    final_urls = [url for url in all_urls if url not in already_indexed]

    if not final_urls:
        logger.info("HASIL: Tidak ada URL baru. Semua URL sudah pernah di-index sebelumnya.")
        return

    logger.info(f"HASIL: Menemukan {len(final_urls)} URL baru untuk dikirim ke Google.")

    # 4. Kirim ke Google
    send_to_google(final_urls)
    logger.info("Selesai.")

if __name__ == "__main__":
    run_indexer()
