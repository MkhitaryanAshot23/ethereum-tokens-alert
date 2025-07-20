import os
import requests
import json
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_URL = "https://api.geckoterminal.com/api/v2/networks/eth/new_pools"
DATA_FILE = "processed_tokens.json"


def get_new_tokens():
    """Получает новые токены Ethereum"""
    try:
        response = requests.get(API_URL)
        if response.status_code != 200:
            print("❌ API вернул ошибку. Код:", response.status_code)
            return []

        data = response.json()
        pools = data.get("data", [])

        new_tokens = []

        for pool in pools:
            base_token_data = pool.get("relationships",
                                       {}).get("base_token",
                                               {}).get("data", {})
            token_id = base_token_data.get("id", "")

            if token_id.startswith("eth_"):
                token_address = token_id[4:]  # убираем префикс 'eth_'
                new_tokens.append(token_address)

        return new_tokens

    except Exception as e:
        print("❌ Ошибка при получении токенов:", e)
        return []


def load_processed_tokens():
    """Загружает уже обработанные токены"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_processed_tokens(tokens):
    """Сохраняет обработанные токены"""
    with open(DATA_FILE, "w") as f:
        json.dump(tokens, f, indent=2)


def send_telegram_message(message):
    """Отправляет сообщение в Telegram"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Bot Token или Chat ID не заданы")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}

    try:
        response = requests.post(url, json=payload)
        if response.json().get("ok"):
            print("✅ Уведомление отправлено")
        else:
            print("❌ Ошибка Telegram API:", response.json())
    except Exception as e:
        print("❌ Ошибка при отправке уведомления:", e)


def main():
    print("🚀 Получаем новые токены Ethereum...")
    tokens = get_new_tokens()

    if not tokens:
        print("💤 Новых токенов нет")
        return

    processed = load_processed_tokens()
    new_tokens = []

    for token_address in tokens:
        if token_address not in processed:
            new_tokens.append(token_address)
            processed[token_address] = {
                "first_seen": datetime.now().isoformat(),
                "notified": True
            }

    if not new_tokens:
        print("🔔 Все токены уже обработаны")
        return

    print(f"✅ Новых токенов: {len(new_tokens)}")

    for token_address in new_tokens:
        message = f"""
🆕 *Новый токен Ethereum*

🔗 [Etherscan](https://etherscan.io/address/{token_address})
"""
        send_telegram_message(message)

    save_processed_tokens(processed)


if __name__ == "__main__":
    main()