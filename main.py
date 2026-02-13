import feedparser
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import json
import os
import logging
import sys
from tqdm import tqdm  # Import tqdm untuk progress bar

# --- 1. KONFIGURASI LOGGING ---
# Setup logging di awal script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- PENGATURAN URL ---

RSS_FEEDS = [
    "https://zero-1pmovie-world.blogspot.com/feeds/posts/default?alt=rss",
]

MANUAL_URLS = [
    "https://my-romance-scammer-the-series.readme.io/reference/my-romance-scammer-ep-3-uncut-hd",
    "https://my-romance-scammer-the-series.readme.io/reference/watch-my-romance-scammer-ep-3-free",
    "https://my-romance-scammer-the-series.readme.io/reference/my-romance-scammer-ep-3-rewatch-thai",
    "https://my-romance-scammer-the-series.readme.io/update/reference/รักจริง-หลังแต่ง-my-romance-scammer-ep-3-uncut",
    "https://melody-of-secrets-uncut.readme.io/reference/ความลับในบทเพลงที่บรรเลงไม่รู้จบ-ep-10-uncut",
    "https://melody-of-secrets-uncut.readme.io/reference/ความลับในบทเพลง-melody-of-secrets-ep-10-uncut",
    "https://melody-of-secrets-uncut.readme.io/reference/melody-of-secrets-ep-10-uncut-full",
    "https://melody-of-secrets-uncut.readme.io/reference/watch-melody-of-secrets-ep-10-free",
    "https://melody-of-secrets-uncut.readme.io/reference/melody-of-secrets-ep-10-rewatch-hd",
    "https://love-alert-the-series.readme.io/reference/watch-love-alert-ep-8-online-free",
    "https://love-alert-the-series.readme.io/reference/มีคําเตือน-โปรดระมัดระวัง-ep-8-uncut-hd",
    "https://duang-with-you-the-series.readme.io/reference/duang-with-you-ep-3",
    "https://muteluv-love-me-if-you-swear.readme.io/reference/muteluv-ตอน-9-วัด-ปะล่ะ-ep-2-uncut",
    "https://muteluv-love-me-if-you-swear.readme.io/reference/watch-muteluv-love-me-if-you-swear-ep-2-uncut",
    "https://muteluv-love-me-if-you-swear.readme.io/reference/muteluv-ตอน-9-วัด-ปะล่ะ-muteluv-love-me-if-you-swear-ep-2",
    "https://yesterday-the-series.readme.io/reference/รอยรักวันวาน-yesterday-ep-2-uncut",
    "https://yesterday-the-series.readme.io/reference/รอยรัก-วันวาน-yesterday-ep-2",
    "https://yesterday-the-series.readme.io/reference/yesterday-ep-2",
]

# --- PROSES INDEXING ---

def send_to_google(urls):
    if not urls:
        logger.warning("Tidak ada URL untuk dikirim.")
        return

    # Ambil kunci dari brankas GitHub Secrets
    try:
        info = json.loads(os.environ['INDEXER_CONFIG'])
        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/indexing"]
        )
        logger.info("Kredensial Google Cloud berhasil dimuat.")
    except KeyError:
        logger.error("Secret 'INDEXER_CONFIG' tidak ditemukan di environment.")
        return

    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    
    # --- TAMBAHKAN TQDM DI SINI ---
    logger.info(f"Memulai pengiriman {len(urls)} URL ke Google Indexing API...")
    
    for url in tqdm(urls, desc="Progress Indexing", unit="url"):
        try:
            credentials.refresh(Request())
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {credentials.token}"
            }
            data = {"url": url, "type": "URL_UPDATED"}
            res = requests.post(endpoint, headers=headers, json=data)
            
            # Jika ingin tetap melihat log per url tanpa merusak bar, gunakan tqdm.write
            if res.status_code != 200:
                tqdm.write(f"Gagal [{res.status_code}] : {url}")
                
        except Exception as e:
            tqdm.write(f"Error pada {url}: {e}")

def run_indexer():
    all_urls = []

    # Ambil link dari semua RSS
    for rss in RSS_FEEDS:
        logger.info(f"Mengecek RSS: {rss}")
        feed = feedparser.parse(rss)
        for entry in feed.entries[:10]:
            all_urls.append(entry.link)

    # Tambahkan link manual
    logger.info(f"Menambahkan {len(MANUAL_URLS)} link manual.")
    all_urls.extend(MANUAL_URLS)

    # Hapus duplikat
    final_urls = list(set(all_urls))
    logger.info(f"Total: {len(final_urls)} link unik siap dikirim.")

    # Jalankan pengiriman
    send_to_google(final_urls)
    logger.info("Proses selesai seluruhnya.")

if __name__ == "__main__":
    run_indexer()
