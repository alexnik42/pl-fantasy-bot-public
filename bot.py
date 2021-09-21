from datetime import datetime, timezone
from flask import Flask, request
import telebot
import time
import os
import logging
import threading
from time_conversions import *
from update_deadline import *
from parse_gameweeks import *

TOKEN = os.getenv('TOKEN')
BOT_URL = os.getenv('BOT_URL')

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 'Greetings!\n' +
        'Type /help to list available commands.\n'
    )


@bot.message_handler(commands=['help'])
def send_commands(message):
    bot.send_message(
        message.chat.id, '*Available commands:*\n\n' +
        '/deadline' + ' - To subscribe to deadline notifications. ' +
        'Bot will send notifications 2 days, 1 day, 6 hours, 2 hours and 1 hour before deadline\n',
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['deadline'])
def send_deadline(message):
    msg = ''
    gameweeks = parse_gameweeks()
    curr_date = datetime.now(timezone.utc)
    for deadline, name in gameweeks:
        if (deadline - curr_date).total_seconds() > 0:
            msg = "Deadline for {} ({} Moscow Time) is in *{}*".format(name, utc_to_local(deadline).strftime(
                '%d, %b %Y, %H:%M:%S'), parse_seconds((deadline - curr_date).total_seconds()))
            break
    if msg != '':
        bot.send_message(message.chat.id, msg, parse_mode='Markdown')

    def get_fixtures():
        current_hour = datetime.now().hour
        while True:
            time.sleep(15)
            if datetime.now().hour() % 8 == 0:
                gameweeks = parse_gameweeks()
            if datetime.now().hour != current_hour:
                current_hour = datetime.now().hour
                msg = update_deadline(gameweeks)
                if msg != "":
                    bot.send_message(message.chat.id, msg,
                                     parse_mode='Markdown')
    for th in threading.enumerate():
        if th.name == "{}_{}".format("deadline", message.chat.id):
            break
    else:
        subscribe_to_notifications = threading.Thread(target=get_fixtures,
                                                      name="{}_{}".format("deadline", message.chat.id))
        subscribe_to_notifications.start()


# Define logger
logger = logging.getLogger('fantasy_deadline_log')
logger.setLevel(logging.INFO)

fh = logging.FileHandler("errors.log")
fh.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

logger.addHandler(fh)

# Run bot
if __name__ == '__main__':
    logger.info('Bot running...\n')

    @server.route('/' + TOKEN, methods=['POST'])
    def getMessage():
        bot.process_new_updates(
            [telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return '?', 200

    @server.route('/')
    def webhook():
        bot.remove_webhook()
        bot.set_webhook(
            url=BOT_URL + TOKEN)
        return '!', 200
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
