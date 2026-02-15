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
    "https://love-me-if-you-swear-ep2.readme.io/reference/muteluv-ep2-9วัดปะล่ะ-ดูฟรี",
    "https://love-me-if-you-swear-ep2.readme.io/reference/love-me-if-you-swear-ep2-thai",
    "https://love-me-if-you-swear-ep2.readme.io/reference/muteluv-ep3-9วัดปะล่ะ-ดูฟรี",
    "https://love-me-if-you-swear-ep2.readme.io/reference/love-me-if-you-swear-ep3-thai",
    "https://yesterday-bl-series.readme.io/reference/รอยรักวันวาน-ep2-พากย์ไทย-2026",
    "https://yesterday-bl-series.readme.io/reference/yesterday-series-ep2-thai-dub",
    "https://yesterday-bl-series.readme.io/reference/รอยรักวันวาน-ep3-พากย์ไทย-2026",
    "https://yesterday-bl-series.readme.io/reference/yesterday-series-ep3-thai-dub",
    "https://peach-lover-ep5-uncut-thai.readme.io/reference/ลูกพีชทานสด-ep5-พากย์ไทย-full-hd",
    "https://peach-lover-ep5-uncut-thai.readme.io/reference/peach-lover-ep5-uncut-thai",
    "https://cat-for-cash-ep5-thai-dub.readme.io/reference/เปย์รักด้วยแมวเลี้ยง-ep5-ดูฟรี-uncut",
    "https://cat-for-cash-ep5-thai-dub.readme.io/reference/cat-for-cash-ep5-thai-dub",
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
