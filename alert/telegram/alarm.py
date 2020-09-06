#!/usr/bin/python3

import telebot
import time
import sys
import os.path
import json
import logging
import logging.config
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from common.timestamp import current_timestamp
import common.vars as variables
from store.store_api import StoreApi
from store.store_api import StoreApiException


class TelegramAlarm:
    def __init__(self):
        self.logger = logging.getLogger("TelegramAlarm")
        self.logger.info("Creating TelegramAlarm")
        self.db = StoreApi()
        with open(variables.TOKEN_PATH, 'r') as f:
            token = f.readline()
        self.bot = telebot.TeleBot(token)

    def update_item_alert(self, item):
        self.logger.info(f"Updating item's alert: {item}")
        self.db.update_alert(item)

    def send_alarm(self, chat_id, fmt, item, book):
        self.logger.info(f"Sending alarm to the user {chat_id} with the format '{fmt}' because of the book {book}")
        msg = self.parse(item, book, fmt)
        self.bot.send_message(chat_id, msg, parse_mode="HTML")
        self.update_item_alert(item)

    def parse(self, item, book, fmt):
        self.logger.info(f"Parsing item: {item}, book: {book}, fmt: '{fmt}'")
        for key in book.keys():
            fmt = fmt.replace("$" + key, str(book[key]))

        for key in item.keys():
            fmt = fmt.replace("$" + key, str(item[key]))
        self.logger.info(f"The result of parsing: '{fmt}'")
        return fmt

    """ SELECT
            tracks.chat_id,
            representations.format,
            books.*
        FROM
            books
        INNER JOIN
            alerts
        ON 1=1
            AND COALESCE(alerts.time, -INF) < book.last_modify_dttm
            AND book.last_modify_dttm >= prev_last_modify_dttm - 1 day
            AND COALESCE(alerts.url, book.url) = books.url
        INNER JOIN
            tracks
        ON 1=1
            AND books.url = tracks.url
        INNER JOIN
            representations
        ON 1=1
            AND representations.id = books.platform
    """
    def run(self):
        self.logger.info(f"Run alarm.")

        for represent in self.db.get_platforms():
            self.logger.debug(f"represent: {represent}")
            for item in self.db.get_items_by_platform(represent["platform"]):
                self.logger.debug(f"item: {item}")
                book = self.db.get_book_by_item(item)
                self.logger.debug(f"book: {book}")
                if book is None:
                    self.logger.warning(f"There is Item {item} without book in DB")
                    continue
                alert = self.db.get_alert_by_book(book)
                self.logger.debug(f"alert: {alert}")
                if alert is None or alert["inc_field"] < item["inc_field"]:
                    self.logger.info(f"The book {book} has been updated. Sending alerts.")
                    for track in self.db.get_tracks_by_book(book):
                        self.send_alarm(track["chat_id"], represent["format"], item, book)
                else:
                    self.logger.info(f"No updates on the book {book}.")

        self.logger.info(f"Finish alarm.")


if __name__ == "__main__":
    with open(variables.LOGGING_CONF_FILE_PATH, "r") as f:
        conf_dict = json.load(f)
    logging.config.dictConfig(conf_dict)
    alarm = TelegramAlarm()
    alarm.run()
