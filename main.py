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
    "https://mickey-17-koreansub.readme.io/reference/mickey-17-bong-joon-ho-info",
    "https://mickey-17-koreansub.readme.io/reference/watch-mickey-17-ott-korea-info",
    "https://the-roundup-5-koreansub.readme.io/reference/the-roundup-5-villain-release-info",
    "https://the-roundup-5-koreansub.readme.io/reference/watch-the-roundup-5-korea-movie",
    "https://hope-koreansub.readme.io/reference/hope-movie-na-hong-jin-korea-info",
    "https://hope-koreansub.readme.io/reference/watch-hope-korea-movie-streaming-info",
    "https://omniscient-reader-korean-movie.readme.io/reference/omniscient-reader-movie-cast-info",
    "https://omniscient-reader-korean-movie.readme.io/reference/watch-omniscient-reader-korean-movie",
    "https://scream-7-koreansub-2026.readme.io/reference/scream-7-korea-release-date-info",
    "https://scream-7-koreansub-2026.readme.io/reference/watch-scream-7-korean-sub-ott-uncut",
    "https://zootopia-2-koreansub.readme.io/reference/zootopia-2-dubbing-release-info",
    "https://zootopia-2-koreansub.readme.io/reference/watch-zootopia-2-korea-dubbing",
    "https://sup-pa-rer-2-uhd.readme.io/reference/สัปเหร่อ-2-เต็มเรื่อง-hd",
    "https://thai-movie-the-undertaker-2.readme.io/reference/สัปเหร่อ-2-uhd",
    "https://thai-movie-the-undertaker-2.readme.io/reference/สัปเหร่อ-2-ซับไทย-4k",
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
