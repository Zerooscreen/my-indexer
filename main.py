import feedparser
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import json
import os

# GANTI URL DI BAWAH INI DENGAN URL BLOG ANDA
RSS_URL = "https://zero-lpmovie-world.blogspot.com/feeds/posts/default?alt=rss"

def run_indexer():
    print("Mengecek artikel terbaru...")
    feed = feedparser.parse(RSS_URL)
    urls = [entry.link for entry in feed.entries[:10]] 
    print(f"Ditemukan {len(urls)} link.")

    if not urls:
        print("Tidak ada link ditemukan. Cek kembali RSS URL Anda.")
        return

    # Ambil kunci dari brankas GitHub Secrets
    info = json.loads(os.environ['INDEXER_CONFIG'])
    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/indexing"]
    )

    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    for url in urls:
        credentials.refresh(Request())
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {credentials.token}"
        }
        data = {"url": url, "type": "URL_UPDATED"}
        res = requests.post(endpoint, headers=headers, json=data)
        print(f"Status {res.status_code} untuk: {url}")

if __name__ == "__main__":
    run_indexer()
