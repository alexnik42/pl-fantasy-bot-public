import logging
import requests
from typing import Optional, Union

from .config import get_token


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)


def get_bot_url() -> str:
    token = get_token()
    return f"https://api.telegram.org/bot{token}/"


def send_message(chat_id: Union[int, str], text: str, parse_mode: Optional[str] = None) -> None:
    url = get_bot_url() + "sendMessage"
    params = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        params["parse_mode"] = parse_mode
    try:
        response = requests.get(url, params=params, timeout=15)
        _logger.info("Telegram response: %s", response.text)
        response.raise_for_status()
    except Exception as exc:
        _logger.error("Failed to send Telegram message to %s: %s", chat_id, exc) 