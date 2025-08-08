import logging
from datetime import datetime, timezone

from app.services.config import (
    get_broadcast_chat_ids,
    get_deadline_alert_tolerance_seconds,
    get_deadline_alert_windows_minutes,
)
from app.services.fpl_utils import fetch_gameweeks, seconds_to_dhms_string, should_alert
from app.services.telegram_utils import send_message


logging.getLogger().setLevel(logging.INFO)


def lambda_handler(event, context):
    gameweeks = fetch_gameweeks()
    logging.info("Found %s gameweeks", (0 if not gameweeks else len(gameweeks)))
    now = datetime.now(timezone.utc)

    windows_minutes = get_deadline_alert_windows_minutes()
    tolerance_seconds = get_deadline_alert_tolerance_seconds()

    for deadline, name in gameweeks:
        time_to_deadline = (deadline - now).total_seconds()
        if time_to_deadline > 0:
            if should_alert(time_to_deadline, windows_minutes, tolerance_seconds):
                logging.info("Time to deadline: %ss", time_to_deadline)
                msg = (
                    "Deadline for {} ({} UTC time) is in *{}*".format(
                        name,
                        deadline.strftime('%A, %d %b %Y, %H:%M:%S'),
                        seconds_to_dhms_string(time_to_deadline),
                    )
                )
                logging.info("Broadcasting message: %s", msg)
                for chat_id in get_broadcast_chat_ids():
                    try:
                        send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                    except Exception as e:
                        logging.error("Unsuccessful sending to %s, error: %s", chat_id, e)
            break

    return {
        'statusCode': 200,
    } 