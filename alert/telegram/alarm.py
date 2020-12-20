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

    def send_alarm(self, chat_id, fmt, item, book):
        self.logger.info(f"Sending alarm to the user {chat_id} with the format '{fmt}' because of the book {book}")
        msg = self.parse(item, book, fmt)
        self.bot.send_message(chat_id, msg, parse_mode="HTML", disable_notification=True)
        # self.update_item_alert(item)

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
        try:
            for user in self.db.get_users():
                self.process_user(user)

        except StoreApiException as ex:
            self.logger.critical(f"There is exception occurred during communication with DB")
            self.logger.exception(ex)

        self.logger.info(f"Finish alarm.")

    def process_book(self, user, book):
        if book.get("pause", True):
            self.logger.info(f"User {user['chat_id']} paused his notifications for book {book}")
            return False
        item = self.db.get_item_by_book(book)
        if item is None:
            self.logger.warning(f"Book {book} has no item")
            return False
        if book.get("inc_field") is None or book["inc_field"] < item["inc_field"]:
            self.logger.info(f"Updating book for user: {user['chat_id']}, old book: {book}, item: {item}")
            book["inc_field"] = item["inc_field"]
            book["platform"] = item["source_crawler"]
            book["description"] = item.get("description")
            book["name"] = item.get("name")
            book["last_modify_dttm"] = item.get("last_modify_dttm")
            book["processed_dttm"] = item.get("processed_dttm")
            item_last_chapter_index = item.get("last_chapter_index", 0) \
                if item.get("last_chapter_index", 0) is not None \
                else 0
            book_last_chapter_index = book.get("last_chapter_index", 0) \
                if book.get("last_chapter_index", 0) is not None \
                else 0
            diff_last_chapter_index = int(item_last_chapter_index) - int(book_last_chapter_index)
            book["diff_last_chapter_index"] = diff_last_chapter_index
            book["last_chapter_index"] = item.get("last_chapter_index")
            item_last_pages_number = item.get("last_pages_number", 0) \
                if item.get("last_pages_number", 0) is not None \
                else 0
            book_last_pages_number = book.get("last_pages_number", 0) \
                if book.get("last_pages_number", 0) is not None \
                else 0
            diff_last_pages_number = int(item_last_pages_number) - int(book_last_pages_number)
            book["diff_last_pages_number"] = diff_last_pages_number
            book["last_pages_number"] = item.get("last_pages_number")
            book["last_relative_modify_dttm"] = item.get("last_relative_modify_dttm")
            fmt = self.db.get_platform_representaion(book["platform"])
            self.send_alarm(user["chat_id"], fmt, item, book)
            return True
        else:
            # TODO: update last_update etc..
            return False

    def process_user(self, user, force_notification=False):
        is_user_modified = False
        if user.get("pause") == True and force_notification == False:
            self.logger.info(f"User {user['chat_id']} paused his notifications")
            return
        for book_url in user["books"].keys():
            book = user["books"][book_url]
            is_user_modified = is_user_modified or self.process_book(user, book)

        if is_user_modified:
            self.logger.info(f"Updating user: {user}")
            self.db.update_user_alerts(user)
        else:
            self.logger.info(f"Nothing to update for user: {user}")


if __name__ == "__main__":
    with open(variables.LOGGING_CONF_FILE_PATH, "r") as f:
        conf_dict = json.load(f)
    logging.config.dictConfig(conf_dict)
    try:
        alarm = TelegramAlarm()
        alarm.run()
    except Exception as ex:
        logger = logging.getLogger("TelegramAlarm")
        logger.critical("The Alarm stopped due to an unknown exception.")
        logger.exception(ex)