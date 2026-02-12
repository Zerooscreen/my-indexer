import feedparser
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import json
import os

# --- PENGATURAN URL ---

# 1. Daftar RSS Feed Blog (Untuk otomatisasi artikel baru)
RSS_FEEDS = [
    "https://zero-1pmovie-world.blogspot.com/feeds/posts/default?alt=rss",
    # "https://blog-lain.blogspot.com/feeds/posts/default?alt=rss", # Tambah di sini jika ada blog lain
]

# 2. Daftar URL Manual (Untuk link spesifik seperti readme.io Anda)
MANUAL_URLS = [
    "https://supparer-2-2569.readme.io/reference/สัปเหร่อ2-เต็มเรื่อง",
    "https://supparer-2-2569.readme.io/reference/สัปเหร่อ-2-fhd",
    "https://undertaker-2-2026.readme.io/reference/the-undertaker-2026-สัปเหร่อ-2",
    "https://undertaker-2-2026.readme.io/reference/the-undertaker-2-เต็มเรื่อง-พากย์ไทย",
    "https://sup-pa-rer-2-hd.readme.io/reference/สัปเหร่อ-2-full-hd",
    "https://sup-pa-rer-2-hd.readme.io/reference/สัปเหร่อ-2-fhd",
    "https://sup-pa-rer-2-hd-2569.readme.io/reference/สัปเหร่อ-2-uhd-พากย์ไทย",
    "https://sup-pa-rer-2-hd-2569.readme.io/reference/sup-pa-rer-2-ซับไทย-ดูฟรี"
	"https://cat-for-cash-the-series-hd.readme.io/reference/ปย์รักด้วยแมวเลี้ยง-ep-4-ย้อนหลัง",
    "https://cat-for-cash-the-series-hd.readme.io/reference/cat-for-cash-ep-4",
    "https://cat-for-cash-the-series-hd.readme.io/reference/เปย์รักด้วยแมวเลี้ยง-cat-for-cash-ep-4-uncut",
    "https://peach-lover-the-series-hd.readme.io/reference/ลูกพีชทานสด-ep-4-uncut",
    "https://peach-lover-the-series-hd.readme.io/reference/ลูกพีชทานสด-ep-4-ย้อนหลัง",
    "https://peach-lover-the-series-hd.readme.io/reference/peach-lover-ep-4",
    "https://yesterday-the-series-hd.readme.io/reference/รอยรักวันวาน-ep-1-ย้อนหลัง",
    "https://yesterday-the-series-hd.readme.io/reference/yesterday-ep-1",
    "https://yesterday-the-series-hd.readme.io/reference/รอยรักวันวาน-ep-1-uncut",
    "https://dare-you-death-the-series-hd.readme.io/reference/ไขคดีเป็น-เห็นคดีตาย-ep-8-ย้อนหลัง",
    "https://dare-you-death-the-series-hd.readme.io/reference/dare-you-to-death-ep-8-bl-uncut-full",
    "https://dare-you-death-the-series-hd.readme.io/reference/ไขคดีเป็น-เห็นคดีตาย-ep-8-uncut",

]

# --- PROSES INDEXING ---

def send_to_google(urls):
    if not urls:
        return

    # Ambil kunci dari brankas GitHub Secrets
    info = json.loads(os.environ['INDEXER_CONFIG'])
    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/indexing"]
    )

    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    
    for url in urls:
        try:
            credentials.refresh(Request())
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {credentials.token}"
            }
            data = {"url": url, "type": "URL_UPDATED"}
            res = requests.post(endpoint, headers=headers, json=data)
            print(f"Status {res.status_code} untuk: {url}")
        except Exception as e:
            print(f"Gagal mengirim {url}: {e}")

def run_indexer():
    all_urls = []

    # Ambil link dari semua RSS yang didaftarkan
    for rss in RSS_FEEDS:
        print(f"Mengecek RSS: {rss}")
        feed = feedparser.parse(rss)
        for entry in feed.entries[:10]: # Ambil 10 terbaru dari tiap blog
            all_urls.append(entry.link)

    # Tambahkan link manual
    print(f"Menambahkan {len(MANUAL_URLS)} link manual.")
    all_urls.extend(MANUAL_URLS)

    # Hapus duplikat link jika ada
    final_urls = list(set(all_urls))
    print(f"Total ada {len(final_urls)} link unik yang akan dikirim ke Google.")

    # Kirim ke Google
    send_to_google(final_urls)

if __name__ == "__main__":
    run_indexer()
