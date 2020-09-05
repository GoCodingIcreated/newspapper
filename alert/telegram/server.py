import pymongo
import telebot

import sys
import os
from bson.objectid import ObjectId
import json
import logging
import logging.config

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
import common.vars as variables
import store.store_api as store_api

import alert.book_requesters.requester as requester

from alert.book_requesters.requester import BookRequesterException



class Server:
    GET_TRACKS = "Get tracks"
    START_TRACKS = "Start tracking"
    STOP_TRACKS = "Stop tracking"
    NOT_ALLOWED = "Not allowed"

    def __init__(self):
        self.logger = logging.getLogger("Server")
        self.logger.info("Creating Server")
        self.db = store_api.StoreApi()
        self.requester = requester.BookRequester()
        with open(variables.TOKEN_PATH, "r") as f:
            token = f.readline()
            print("token: " + token)
        self.bot = telebot.TeleBot(token)
        self.hello_msg = "Hello! I'm Bot for tracking new chapters on AuthorToday, Litmarket, Webnovel."



        @self.bot.message_handler(commands=['start'])
        def start_message(message):
            self.logger.debug("Got message: " + str(message))
            if not self.has_rights(message.chat.id):
                self.logger.info(f"Sending to user {message.chat.id}, message: {Server.NOT_ALLOWED}")
                self.bot.send_message(message.chat.id, Server.NOT_ALLOWED)
                return
            self.logger.info(f"Sending to user {message.chat.id}, message: {self.hello_msg}")
            self.bot.send_message(message.chat.id, self.hello_msg)

        # TODO: rework: /list command with pretty output
        @self.bot.message_handler(commands=['list'])
        def handler_list(message):
            self.logger.debug("Got message: " + str(message))
            if not self.has_rights(message.chat.id):
                self.logger.info(f"Sending to user {message.chat.id}, message: {Server.NOT_ALLOWED}")
                self.bot.send_message(message.chat.id, Server.NOT_ALLOWED)
                return

            subscriptions = self.get_subscription_list(message.chat.id)
            book_urls = [sub["book_url"] for sub in subscriptions]
            msg = "Subscriptions: \n" + "\n".join(book_urls)
            self.logger.info(f"Sending to user {message.chat.id} message: {msg}")
            self.bot.send_message(message.chat.id, msg)

        # TODO: rework: /platform command with pretty output
        @self.bot.message_handler(commands=['platforms'])
        def handler_platforms(message):
            self.logger.debug("Got message: " + str(message))
            if not self.has_rights(message.chat.id):
                self.logger.info(f"Sending to user {message.chat.id}, message: {Server.NOT_ALLOWED}")
                self.bot.send_message(message.chat.id, Server.NOT_ALLOWED)
                return

            platforms = [p["url"] for p in self.db.get_platforms()]
            msg = f"Available platforms: {', '.join(platforms)}"
            self.logger.info(f"Sending to user {message.chat.id} message: {msg}")
            self.bot.send_message(message.chat.id, msg)

        # TODO: rework: /help command with pretty output
        @self.bot.message_handler(commands=['help'])
        def handler_platform(message):
            self.logger.debug("Got message: " + str(message))
            if not self.has_rights(message.chat.id):
                self.logger.info(f"Sending to user {message.chat.id}, message: {Server.NOT_ALLOWED}")
                self.bot.send_message(message.chat.id, Server.NOT_ALLOWED)
                return

            msg = "Help"
            self.logger.info(f"Sending to user {message.chat.id} message: {msg}")
            self.bot.send_message(message.chat.id, msg)

        # TODO: rework: remove_button id. Button bound with button under book_info message in response to user link
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("add"))
        def callback_add(call):
            self.logger.debug("Got message: " + str(call))
            if not self.has_rights(call.from_user.id):
                self.logger.info(f"Sending to user {call.form_user.id}, message: {Server.NOT_ALLOWED}")
                self.bot.answer_callback_query(call.id, "")
                self.bot.send_message(call.form_user.id, Server.NOT_ALLOWED)
                return

            data = call.data.split()
            if len(data) != 2:
                msg = "Unknown button pressed."
                self.logger.error(f"Unknown call with 'add', call: {call}")
                self.logger.info(f"Sending to user {call.from_user.id} message: {msg}")
                self.bot.answer_callback_query(call.id, "")
                self.bot.send_message(call.from_user.id, msg)
            else:
                book_id = data[1]
                book = self.db.get_book({"_id": ObjectId(book_id)})
                if not self.db.is_subscribed_on_book(call.from_user.id, book["book_url"]):
                    self.db.add_track_book_telegram(call.from_user.id, book)
                    msg = f"Start track book: {book['book_url']}."
                    self.logger.info(f"Sending to user {call.from_user.id} message: {msg}")
                    self.bot.answer_callback_query(call.id, "")
                    self.bot.send_message(call.from_user.id, msg)
                else:
                    msg = f"Book: {book['book_url']} is already tracking."
                    self.logger.info(f"Sending to user {call.from_user.id} message: {msg}")
                    self.bot.answer_callback_query(call.id, "")
                    self.bot.send_message(call.from_user.id, msg)

        # TODO: rework: remove_button id. Button bound with button under book_info message in response to user link
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("remove"))
        def callback_remove(call):
            self.logger.debug("Got call: " + str(call))
            if not self.has_rights(call.from_user.id):
                self.logger.info(f"Sending to user {call.form_user.id}, message: {Server.NOT_ALLOWED}")
                self.bot.answer_callback_query(call.id, "")
                self.bot.send_message(call.form_user.id, Server.NOT_ALLOWED)
                return

            data = call.data.split()
            if len(data) != 2:
                msg = "Unknown button pressed."
                self.logger.error(f"Unknown call with 'remove', call: {call}")
                self.logger.info(f"Sending to user {call.from_user.id} message: {msg}")
                self.bot.answer_callback_query(call.id, "")
                self.bot.send_message(call.from_user.id, msg)
            else:
                book_id = data[1]
                book = self.db.get_book({"_id": ObjectId(book_id)})
                if self.db.is_subscribed_on_book(call.from_user.id, book["book_url"]):
                    self.db.remove_track_book_telegram(call.from_user.id, book)
                    msg = f"Stopped track book: {book['book_url']}."
                    self.logger.info(f"Sending to user {call.from_user.id} message: {msg}")
                    self.bot.answer_callback_query(call.id, "")
                    self.bot.send_message(call.from_user.id, msg)
                else:
                    msg = f"Book {book['book_url']} is already not tracking."
                    self.logger.info(f"Sending to user {call.from_user.id} message: {msg}")
                    self.bot.answer_callback_query(call.id, "")
                    self.bot.send_message(call.from_user.id, msg)

        # message itself is a valid link to one of supported platform
        @self.bot.message_handler(func=lambda message: self.check_link(message.text))
        def insert_link(message):
            self.logger.debug("Got message: " + str(message))
            if not self.has_rights(message.chat.id):
                self.logger.info(f"Sending to user {message.chat.id} message {Server.NOT_ALLOWED}")
                self.bot.send_message(message.chat.id, Server.NOT_ALLOWED)
                return

            try:
                book_info = self.requester.request_book(message.text, force_request=False)

                if book_info is None:
                    msg = f"Sorry, but book {message.text} was not found."
                    self.logger.info(f"Sending to user {message.chat.id} message: {msg}")
                    self.bot.send_message(message.chat.id, msg)
                else:
                    book_url = book_info["book_url"]
                    if self.db.is_subscribed_on_book(message.chat.id, book_url):
                        self.logger.info(f"User {message.chat.id} asked to remove subscription on book {book_url}")
                        keyboard = self.get_remove_button_keyboard(book_info["_id"])
                        msg = "\n".join([f"{key}: {book_info[key]}" for key in book_info.keys() if key != "_id"])
                        msg = "Book info:\n" + msg
                        self.logger.info(f"Sending to user {message.chat.id} message: {msg}")
                        self.bot.send_message(message.chat.id, msg, reply_markup=keyboard)
                    else:
                        self.logger.info(f"User {message.chat.id} asked to add subscription on book {book_url}")
                        self.db.add_book(book_info)
                        book = self.db.get_book(book_info)
                        keyboard = self.get_add_button_keyboard(book["_id"])
                        msg = "\n".join([f"{key}: {book_info[key]}" for key in book_info.keys() if key != "_id"])
                        msg = "Book info:\n" + msg
                        self.logger.info(f"Sending to user {message.chat.id} message: {msg}")
                        self.bot.send_message(message.chat.id, msg, reply_markup=keyboard)

            except BookRequesterException as ex:
                self.logger.error("Exception occurred when request book from requester.")
                self.logger.exception(ex)
                msg = "Sorry, but book was not found or maybe link is not for one of valid platform."
                self.logger.info(f"Sending to user {message.chat.id} message: {msg}")
                self.bot.send_message(message.chat.id, msg)

        self.start_polling()

    def start_polling(self):
        self.bot.polling()

    def get_subscription_list(self, user_id):
        return self.db.get_subscriptions(str(user_id))

    def has_rights(self, user_id):
        return self.db.has_user(str(user_id))

    def check_link(self, link):
        # TODO: add method's body
        return True

    @staticmethod
    def get_add_button_keyboard(book_id):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton("Add", callback_data=f"add {book_id}"))
        return keyboard

    @staticmethod
    def get_remove_button_keyboard(book_id):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton("Remove", callback_data=f"remove {book_id}"))
        return keyboard



if __name__ == "__main__":
    with open(variables.LOGGING_CONF_FILE_PATH, "r") as f:
        conf_dict = json.load(f)
    logging.config.dictConfig(conf_dict)

    server = Server()
