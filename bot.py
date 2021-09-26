from datetime import datetime, timezone
from flask import Flask, request
import telebot
import os
import logging
import threading

from time_conversions import *
from update_deadline import *
from parse_gameweeks import *
from handle_subscriptions import *

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
        '/deadline' + ' - To get info on current deadline.\n' +
        '/subscribe' + ' - To subscribe to deadline notifications. ' +
        'Bot will send notifications 2 days, 1 day, 6 hours, 2 hours and 1 hour before deadline\n'
        '/unsubscribe' + ' - To unsubscribe from deadline notifications\n',
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['deadline'])
def send_current_deadline(message):
    msg = ''
    gameweeks = parse_gameweeks()
    curr_date = datetime.now(timezone.utc)
    for deadline, name in gameweeks:
        if (deadline - curr_date).total_seconds() > 0:
            msg = "Deadline for {} ({} Moscow Time) is in *{}*".format(name, utc_to_local(deadline).strftime(
                '%A, %d %b %Y, %H:%M:%S'), parse_seconds((deadline - curr_date).total_seconds()))
            break
    if msg != '':
        bot.send_message(message.chat.id, msg, parse_mode='Markdown')


@bot.message_handler(commands=['subscribe'])
def subscribe_to_notifications(message):
    for th in threading.enumerate():
        if th.name == "{}_{}".format("d", message.chat.id):
            bot.send_message(
                message.chat.id, "You are already subscribed", parse_mode='Markdown')
            break
    else:
        subscribe_to_notifications = threading.Thread(target=send_notifications, args=(message.chat.id, bot, server.logger),
                                                      name="{}_{}".format("d", message.chat.id))
        subscribe_to_notifications.start()
        add_thread_to_file("{}_{}".format("d", message.chat.id))
        bot.send_message(
            message.chat.id, "You successfuly subscribed", parse_mode='Markdown')


@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_to_notifications(message):
    for th in threading.enumerate():
        if th.name == "{}_{}".format("d", message.chat.id):
            remove_thread_from_file(th.name)
            bot.send_message(
                message.chat.id, "You successfuly unsubscribed", parse_mode='Markdown')
            return
    bot.send_message(
        message.chat.id, "You are not subscribed", parse_mode='Markdown')


# Define logger
logger = logging.getLogger('bot_logs.log')
server.logger.handlers
server.logger.setLevel(logging.INFO)

# Run bot
if __name__ == '__main__':
    server.logger.info('Bot starting...')

    server.logger.info('Restarting threads...')
    restart_threads(server.logger, bot)

    server.logger.info('Configuring server...')

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
