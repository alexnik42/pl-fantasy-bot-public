import json
import logging
from datetime import datetime, timezone

from app.services.fpl_utils import next_deadline_and_name, seconds_to_dhms_string
from app.services.live_table import get_live_table
from app.services.telegram_utils import send_message


logging.getLogger().setLevel(logging.INFO)


def parse_message(event):
    logging.info("Parsing message...")
    if 'body' not in event:
        return None, None
    body = json.loads(event['body'])
    if 'message' not in body:
        return None, None
    message = body['message']

    chat_id = message['chat']['id']
    text = message['text'] if 'text' in message else None

    logging.info("Message parsed")
    return chat_id, text


def lambda_handler(event, context):
    chat_id = None
    try:
        chat_id, text = parse_message(event)
        if chat_id is not None and text is not None:
            logging.info("chat_id: %s, text: %s", chat_id, text)
            normalized = text.lower().strip()

            if normalized in ("/deadline", "/deadline@fantasy_deadline_bot"):
                result = next_deadline_and_name()
                if result:
                    deadline, name = result
                    curr_date = datetime.now(timezone.utc)
                    msg = "Deadline for {} ({} UTC time) is in *{}*".format(
                        name,
                        deadline.strftime('%A, %d %b %Y, %H:%M:%S'),
                        seconds_to_dhms_string((deadline - curr_date).total_seconds()),
                    )
                    logging.info("Sending message: %s", msg)
                    send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

            elif normalized in ("/live_table", "/live_table@fantasy_deadline_bot"):
                # msg = get_live_table(chat_id)
                msg = "Live table mode is not supported yet"
                if msg:
                    logging.info("Sending message: %s", msg)
                    send_message(chat_id=chat_id, text=msg, parse_mode="MarkdownV2")

    except Exception as e:
        logging.exception("Error while processing update: %s", e)
        msg = "Something is wrong. Try again later."
        if chat_id is not None:
            send_message(chat_id=chat_id, text=msg, parse_mode="MarkdownV2")

    return {
        'statusCode': 200,
    } 