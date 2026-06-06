from __future__ import annotations

import json
import logging
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)


def send_telegram_message(bot_token: str, chat_id: str, text: str) -> bool:
    """Envía un mensaje de texto formateado a un grupo, canal o chat de Telegram."""
    if not bot_token or not chat_id:
        logger.warning(
            "Telegram credentials missing. Cannot send message. Token: %s, ChatId: %s",
            "OK" if bot_token else "MISSING",
            "OK" if chat_id else "MISSING",
        )
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")

        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            if res_json.get("ok"):
                logger.info("Message successfully sent to Telegram chat: %s", chat_id)
                return True
            else:
                logger.error("Telegram API returned failure: %s", res_body)
                return False
    except Exception as e:
        logger.error("Failed to send Telegram message to chat %s: %s", chat_id, e)
        return False
