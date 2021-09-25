import json
import threading
import datetime
import time
import os
import dropbox
import io

from parse_gameweeks import *
from update_deadline import *

DEFAULT_THREADS = ['MainThread', 'WorkerThread1',
                   'WorkerThread2', 'PollingThread']
PERSONAL_THREAD = os.getenv('PERSONAL_THREAD')
DROPBOX_TOKEN = os.getenv('DROPBOX_TOKEN')


def add_thread_to_file(name):
    try:
        _, res = dbx.files_download("/threads.json")
        with io.BytesIO(res.content) as stream:
            data = json.load(stream)
    except:
        data = {"threads": {}}

    data["threads"][name] = True
    with io.StringIO() as stream:
        json.dump(data, stream, indent=4)
        stream.seek(0)
        dbx.files_upload(stream.read().encode(), "/threads.json",
                         mode=dropbox.files.WriteMode.overwrite)


def remove_thread_from_file(name):
    try:
        _, res = dbx.files_download("/threads.json")
        with io.BytesIO(res.content) as stream:
            data = json.load(stream)
    except:
        data = {"threads": {}}

    if name in data["threads"]:
        del data["threads"][name]
    with io.StringIO() as stream:
        json.dump(data, stream, indent=4)
        stream.seek(0)
        dbx.files_upload(stream.read().encode(), "/threads.json",
                         mode=dropbox.files.WriteMode.overwrite)


def is_thread_active(name):
    try:
        _, res = dbx.files_download("/threads.json")
        with io.BytesIO(res.content) as stream:
            data = json.load(stream)
    except:
        data = {"threads": {}}
    return name in data["threads"]


def restart_threads(logger, bot):
    try:
        _, res = dbx.files_download("/threads.json")
        with io.BytesIO(res.content) as stream:
            data = json.load(stream)
            for th in data["threads"]:
                if th[:2] == "d_":
                    subscribe_to_notifications = threading.Thread(target=send_notifications, args=(th[2:], bot, logger),
                                                                  name=th)
                    subscribe_to_notifications.start()
    except FileNotFoundError:
        logger.info("No threads exist")


def send_notifications(chat_id, bot, logger):
    gameweeks = parse_gameweeks()
    msg = ""
    saved_minute = datetime.now().minute
    while True:
        time.sleep(15)
        if not is_thread_active(threading.current_thread().name):
            return

        # Avoid duplicate logging in case of multiple threads
        if threading.current_thread().name == PERSONAL_THREAD:
            logger.info("Current threads include [{}]".format(", ".join(
                [th.name for th in threading.enumerate() if th.name not in DEFAULT_THREADS])))

        if datetime.now().hour % 8 == 0:
            gameweeks = parse_gameweeks()

        curr_minute = datetime.now().minute
        if curr_minute % 30 == 0 and curr_minute != saved_minute:
            saved_minute = curr_minute
            msg = update_deadline(gameweeks, curr_minute)
            if msg != "":
                try:
                    bot.send_message(chat_id, msg,
                                     parse_mode='Markdown')
                except:
                    remove_thread_from_file(threading.current_thread().name)
                    return


def connect_to_dropbox():
    try:
        dbx = dropbox.Dropbox(DROPBOX_TOKEN)
        print('Connected to Dropbox successfully')

    except Exception as e:
        print(str(e))

    return dbx


dbx = connect_to_dropbox()
