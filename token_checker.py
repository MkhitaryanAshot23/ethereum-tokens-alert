import os
import requests
import json
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_new_tokens():
    try:
        response = requests.get("https://api.geckoterminal.com/api/v2/networks/eth/new_pools")
        if response.status_code != 200:
            print("❌ API вернул ошибку. Код:", response.status_code)
            return []

        data = response.json()
        pools = data.get("data", [])
        return [pool.get("relationships", {}).get("base_token", {}).get("data", {}).get("id", "")[4:] for pool in pools if pool.get("relationships", {}).get("base_token", {}).get("data", {}).get("id", "").startswith("eth_")]

    except Exception as e:
        print("❌ Ошибка при получении токенов:", e)
        return []

def load_processed_tokens():
    if os.path.exists("processed_tokens.json"):
        with open("processed_tokens.json", "r") as f:
            return json.load(f)
    return {}

def save_processed_tokens(tokens):
    with open("processed_tokens.json", "w") as f:
        json.dump(tokens, f, indent=2)

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Bot Token или Chat ID не заданы")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        requests.post(url, json=payload)
        print("✅ Уведомление отправлено")
    except Exception as e:
        print("❌ Ошибка при отправке:", e)

def main():
    print("🔄 Запуск мониторинга Ethereum токенов в", datetime.now().isoformat())
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