import requests
from config import TELEGRAM_TOKEN, CHAT_IDS


def send_alert(message: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    all_ok = True
    for chat_id in CHAT_IDS:
        try:
            r = requests.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "disable_web_page_preview": True,
            }, timeout=10)
            if not r.ok:
                print(f"[notifier] error chat {chat_id}: {r.text[:100]}")
                all_ok = False
        except requests.RequestException as e:
            print(f"[notifier] error chat {chat_id}: {e}")
            all_ok = False
    return all_ok
