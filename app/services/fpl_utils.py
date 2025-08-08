import logging
from datetime import datetime, timezone
from typing import List, Tuple, Optional

import dateutil.parser
import requests

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)


def fetch_gameweeks() -> List[Tuple[datetime, str]]:
    res = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=20)
    res = res.json()
    gameweeks = [
        (dateutil.parser.isoparse(r["deadline_time"]).replace(tzinfo=timezone.utc), r["name"]) for r in res["events"]
    ]
    return gameweeks


def seconds_to_dhms_string(total_seconds: float) -> str:
    n = int(total_seconds)
    day = n // (24 * 3600)
    n = n % (24 * 3600)
    hour = n // 3600
    n %= 3600
    minutes = n // 60
    n %= 60
    seconds = n
    return f"{int(day)} days, {int(hour)} hours, {int(minutes)} minutes, {int(seconds)} seconds"


def should_alert(time_to_deadline_seconds: float, windows_minutes: List[int], tolerance_seconds: int) -> bool:
    for minutes in windows_minutes:
        window_seconds = minutes * 60
        if (window_seconds - tolerance_seconds) <= time_to_deadline_seconds <= (window_seconds + tolerance_seconds):
            return True
    return False


def next_deadline_and_name(now: Optional[datetime] = None) -> Optional[Tuple[datetime, str]]:
    gameweeks = fetch_gameweeks()
    current_time = now or datetime.now(timezone.utc)
    for deadline, name in gameweeks:
        delta = (deadline - current_time).total_seconds()
        if delta > 0:
            return deadline, name
    return None 