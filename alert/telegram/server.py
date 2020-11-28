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

from store.store_api import StoreApiException
from store.store_api import StoreApi

import alert.book_requesters.requester as requester
from alert.book_requesters.requester import BookRequesterException


class Server:
    NOT_ALLOWED = "Not allowed"

    def __init__(self):
        self.logger = logging.getLogger("Server")
        self.logger.info("Creating the Server")
        self.db = StoreApi()
        self.requester = requester.BookRequester()
        with open(variables.TOKEN_PATH, "r") as f:
            token = f.readline()

        self.bot = telebot.TeleBot(token)
        remove_keyboard = telebot.types.ReplyKeyboardRemove()

        @self.bot.message_handler(commands=['start'])
        def start_message(message):
            try:
                self.logger.debug("Got a message: " + str(message))
                if not self.has_rights(message.chat.id):
                    self.logger.info(f"Sending to the user {message.chat.id} a message: {Server.NOT_ALLOWED}")
                    self.bot.send_message(message.chat.id, Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                self.logger.info(f"Adding a new user {message.chat.id}")
                try:
                    self.db.add_telegram_user(message.chat.id)
                    platforms = [p["url"] for p in self.db.get_platforms()]
                    msg = f"Hello!\nI'm Bot for tracking new chapters.\n\nAvailable platforms: {', '.join(platforms)}.\n\n" \
                          f"To subscribe/unsubscribe on new a book just send a message with a http link" \
                          f" at the book from one of the available platform.\n\n" \
                          f"Also use following commands to interact with bot:\n" \
                          f"\t/list - Get current subscriptions.\n" \
                          f"\t/platforms - Get list of available platforms.\n" \
                          f"\t/help - Get list of allowed commands.\n"
                    self.logger.info(f"Sending to the the user {message.chat.id} a message: {msg}")
                    self.bot.send_message(message.chat.id, msg, reply_markup=remove_keyboard)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when started an interaction with a new user: {message.chat.id}")
                    self.logger.exception(ex)
                    self.bot.send_message(message.chat.id, "Sorry, an unknown error occurred.", reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the new user: {message.chat.id}")
                self.logger.exception(ex)

        @self.bot.message_handler(commands=['list'])
        def handler_list(message):
            try:
                self.logger.debug("Got a message: " + str(message))
                if not self.has_rights(message.chat.id):
                    self.logger.info(f"Sending to the user {message.chat.id} a message: {Server.NOT_ALLOWED}")
                    self.bot.send_message(message.chat.id, Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    subscriptions = self.get_subscription_list(message.chat.id)
                    book_urls = [sub["book_url"] for sub in subscriptions]
                    msg = "Subscriptions: \n" + "\n\n".join(book_urls)
                    self.logger.info(f"Sending to the user {message.chat.id} a message: {msg}")
                    self.bot.send_message(message.chat.id, msg, reply_markup=remove_keyboard, disable_web_page_preview=True)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when executed '/list' command for the user: {message.chat.id}")
                    self.logger.exception(ex)
                    self.bot.send_message(message.chat.id, "Sorry, an unknown error occurred.", reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the user: {message.chat.id}")
                self.logger.exception(ex)

        @self.bot.message_handler(commands=['pause', 'unpause'])
        def handler_pause(message):
            try:
                self.logger.debug("Got a message: " + str(message))
                if not self.has_rights(message.chat.id):
                    self.logger.info(f"Sending to the user {message.chat.id} a message: {Server.NOT_ALLOWED}")
                    self.bot.send_message(message.chat.id, Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    if message.text == "/pause":
                        self.db.user_pause_alerts({"chat_id": str(message.chat.id)})
                        msg = "Paused notifications for books"
                    elif message.text == "/unpause":
                        self.db.user_unpause_alerts({"chat_id": str(message.chat.id)})
                        msg = "Unpaused notifications for books"
                    else:
                        self.logger.critical(f"Unknown command: {message.text}")
                        return
                    self.logger.info(f"Sending to the user {message.chat.id} a message: {msg}")
                    self.bot.send_message(message.chat.id, msg, reply_markup=remove_keyboard,
                                          disable_web_page_preview=True)

                except StoreApiException as ex:
                    self.logger.error(
                        f"An exception occurred when executed '/pause' command for the user: {message.chat.id}")
                    self.logger.exception(ex)
                    self.bot.send_message(message.chat.id, "Sorry, an unknown error occurred.",
                                          reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the user: {message.chat.id}")
                self.logger.exception(ex)

        @self.bot.message_handler(commands=['platforms'])
        def handler_platforms(message):
            try:
                self.logger.debug("Got a message: " + str(message))
                if not self.has_rights(message.chat.id):
                    self.logger.info(f"Sending to the user {message.chat.id} a message: {Server.NOT_ALLOWED}")
                    self.bot.send_message(message.chat.id, Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    platforms = [p["url"] for p in self.db.get_platforms()]
                    msg = f"Available platforms: {', '.join(platforms)}"
                    self.logger.info(f"Sending to the user {message.chat.id} a message: {msg}")
                    self.bot.send_message(message.chat.id, msg, reply_markup=remove_keyboard)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when executed '/platforms' command for the user: {message.chat.id}")
                    self.logger.exception(ex)
                    self.bot.send_message(message.chat.id, "Sorry, an unknown error occurred.", reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the user: {message.chat.id}")
                self.logger.exception(ex)

        @self.bot.message_handler(commands=['help'])
        def handler_platform(message):
            try:
                self.logger.debug("Got a message: " + str(message))
                if not self.has_rights(message.chat.id):
                    self.logger.info(f"Sending to the user {message.chat.id} a message: {Server.NOT_ALLOWED}")
                    self.bot.send_message(message.chat.id, Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    platforms = [p["url"] for p in self.db.get_platforms()]
                    msg = f"Available platforms: {', '.join(platforms)}.\n\n" \
                              f"To subscribe/unsubscribe on new a book just send a message with a http link" \
                              f" at the book from one of the available platform.\n\n" \
                              f"Also use following commands to interact with bot:\n" \
                              f"\t/list - Get current subscriptions.\n" \
                              f"\t/platforms - Get list of available platforms.\n" \
                              f"\t/help - Get list of allowed commands.\n"
                    self.logger.info(f"Sending to the user {message.chat.id} a message: {msg}")
                    self.bot.send_message(message.chat.id, msg, reply_markup=remove_keyboard, disable_web_page_preview=True)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when executed '/help' command for the user: {message.chat.id}")
                    self.logger.exception(ex)
                    self.bot.send_message(message.chat.id, "Sorry, an unknown error occurred.",
                                          reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the user: {message.chat.id}")
                self.logger.exception(ex)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("add"))
        def callback_add(call):
            try:
                self.logger.debug("Got a message: " + str(call))
                if not self.has_rights(call.from_user.id):
                    self.logger.info(f"Sending to the user {call.form_user.id}, a message: {Server.NOT_ALLOWED}")
                    self.bot.answer_callback_query(call.id, "")
                    self.bot.send_message(call.form_user.id, Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    data = call.data.split()
                    if len(data) != 2:
                        msg = "An unknown button was pressed."
                        self.logger.error(f"An unknown call with 'add', call: {call}")
                        self.logger.info(f"Sending to the user {call.from_user.id} a message: {msg}")
                        self.bot.answer_callback_query(call.id, "")
                        self.bot.send_message(call.from_user.id, msg, reply_markup=remove_keyboard)
                    else:
                        book_id = data[1]
                        book = self.db.get_book({"_id": ObjectId(book_id)})
                        if not self.db.is_subscribed_on_book(call.from_user.id, book["book_url"]):
                            self.db.add_track_book_telegram(call.from_user.id, book)
                            msg = f"Start tracking the book: {book['book_url']}."
                            self.logger.info(f"Sending to the user {call.from_user.id} a message: {msg}")
                            keyboard = self.get_revert_keyboard(call)
                            self.bot.answer_callback_query(call.id, "")
                            self.bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                                               message_id=call.message.message_id,
                                                               reply_markup=keyboard)
                            self.bot.send_message(call.from_user.id, msg, reply_markup=remove_keyboard)
                        else:
                            msg = f"Book: {book['book_url']} has been already tracked."
                            self.logger.info(f"Sending to the user {call.from_user.id} a message: {msg}")
                            keyboard = self.get_revert_keyboard(call)
                            self.bot.answer_callback_query(call.id, "")
                            self.bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                                               message_id=call.message.message_id,
                                                               reply_markup=keyboard)
                            self.bot.send_message(call.from_user.id, msg, reply_markup=remove_keyboard)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when executed '{call.data}' callback for the user: {call.from_user.id}")
                    self.logger.exception(ex)
                    self.bot.send_message(call.from_user.id, "Sorry, an unknown error occurred.", reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the user: {call.from_user.id}")
                self.logger.exception(ex)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("remove"))
        def callback_remove(call):
            try:
                self.logger.debug("Got a call: " + str(call))
                if not self.has_rights(call.from_user.id):
                    self.logger.info(f"Sending to the user {call.form_user.id}, a message: {Server.NOT_ALLOWED}")
                    self.bot.answer_callback_query(call.id, "")
                    self.bot.send_message(call.form_user.id, Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    data = call.data.split()
                    if len(data) != 2:
                        msg = "An unknown button pressed."
                        self.logger.error(f"An unknown call with 'remove', call: {call}")
                        self.logger.info(f"Sending to the user {call.from_user.id} a message: {msg}")
                        self.bot.answer_callback_query(call.id, "")
                        self.bot.send_message(call.from_user.id, msg, reply_markup=remove_keyboard)
                    else:
                        book_id = data[1]
                        book = self.db.get_book({"_id": ObjectId(book_id)})
                        if self.db.is_subscribed_on_book(call.from_user.id, book["book_url"]):
                            self.db.remove_track_book_telegram(call.from_user.id, book)
                            msg = f"Stopped track the book: {book['book_url']}."
                            self.logger.info(f"Sending to the user {call.from_user.id} a message: {msg}")
                            keyboard = self.get_revert_keyboard(call)
                            self.bot.answer_callback_query(call.id, "")
                            self.bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                                               message_id=call.message.message_id,
                                                               reply_markup=keyboard)
                            self.bot.send_message(call.from_user.id, msg, reply_markup=remove_keyboard)
                        else:
                            msg = f"The book {book['book_url']} has been already not tracked."
                            self.logger.info(f"Sending to the user {call.from_user.id} a message: {msg}")
                            keyboard = self.get_revert_keyboard(call)
                            self.bot.answer_callback_query(call.id, "")
                            self.bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                                               message_id=call.message.message_id,
                                                               reply_markup=keyboard)
                            self.bot.send_message(call.from_user.id, msg, reply_markup=remove_keyboard)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when executed '{call.data}' callback from the user: {call.from_user.id}")
                    self.logger.exception(ex)
                    self.bot.send_message(call.from_user.id, "Sorry, an unknown error occurred.", reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the user: {call.from_user.id}")
                self.logger.exception(ex)

        # message itself is a valid link to one of supported platform
        @self.bot.message_handler(func=lambda message: True)
        def insert_link(message):
            try:
                self.logger.debug("Got a message: " + str(message))
                if not self.has_rights(message.chat.id):
                    self.logger.info(f"Sending to the user {message.chat.id} a message {Server.NOT_ALLOWED}")
                    self.bot.send_message(message.chat.id, Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    book_info = self.requester.request_book(message.text, force_request=False)
                    if book_info is None:
                        msg = f"Sorry, but the book {message.text} was not found."
                        self.logger.info(f"Sending to the user {message.chat.id} a message: {msg}")
                        self.bot.send_message(message.chat.id, msg, reply_markup=remove_keyboard, disable_web_page_preview=True)
                    else:
                        book_url = book_info["book_url"]
                        if self.db.is_subscribed_on_book(message.chat.id, book_url):
                            self.logger.info(f"The user {message.chat.id} asked to remove a subscription on the book {book_url}")
                            keyboard = self.get_remove_button_keyboard(book_info["_id"])
                            msg = "\n".join([f"{key}: {book_info[key]}" for key in book_info.keys() if key != "_id"])
                            msg = "The book info:\n" + msg
                            self.logger.info(f"Sending to the user {message.chat.id} a message: {msg}")
                            self.bot.send_message(message.chat.id, msg, reply_markup=keyboard)
                        else:
                            self.logger.info(f"The user {message.chat.id} asked to add a subscription on the book {book_url}")
                            self.db.add_book(book_info)
                            book = self.db.get_book(book_info)
                            keyboard = self.get_add_button_keyboard(book["_id"])
                            msg = "\n".join([f"{key}: {book_info[key]}" for key in book_info.keys() if key != "_id"])
                            msg = "The book info:\n" + msg
                            self.logger.info(f"Sending to the user {message.chat.id} a message: {msg}")
                            self.bot.send_message(message.chat.id, msg, reply_markup=keyboard)

                except BookRequesterException as ex:
                    self.logger.info(f"A book from link {message.text} was not found by the Requester.")
                    msg = "Sorry, but the book was not found or maybe the link is not for one of the valid platform."
                    self.logger.info(f"Sending to the user {message.chat.id} message: {msg}")
                    self.bot.send_message(message.chat.id, msg, reply_markup=remove_keyboard)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when executed 'insert_link' for the user: {message.chat.id}")
                    self.logger.exception(ex)
                    self.bot.send_message(message.chat.id, "Sorry, an unknown error occurred.", reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the user: {message.chat.id}")
                self.logger.exception(ex)

        # self.start_polling()

    def start_polling(self):
        self.bot.polling()

    def get_subscription_list(self, user_id):
        return self.db.get_subscriptions(str(user_id))

    def has_rights(self, user_id):
        return self.db.has_user(str(user_id))

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

    def get_revert_keyboard(self, call):
        self.logger.debug(f"call: {call}")
        try:
            data = call.message.json["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
        except KeyError | IndexError as ex:
            self.logger.error(f"Excepted the InlineKeyboardButton with callback data, call: {call}")
            return None
        self.logger.info(f"data: {data}, call: {call}")
        if data is None:
            self.logger.error(f"Empty data in callback, call: {call}")
            return None

        type, book_id = data.split()
        new_type = None
        button_text = None
        if type == "add":
            new_type = "remove"
            button_text = "Remove"
        elif type == "remove":
            new_type = "add"
            button_text = "Add"
        else:
            self.logger.error(f"Unknown callback type. Expected 'add' or 'remove', got: {type}, call: {call}")
            return None

        new_callback_data = f"{new_type} {book_id}"
        self.logger.info(f"New callback data: {new_callback_data}, button text: {button_text}")
        self.logger.debug(f"call: {call}, new_callback_data: {new_callback_data}, button_text: {button_text}")
        new_keyboard = telebot.types.InlineKeyboardMarkup()
        new_keyboard.add(telebot.types.InlineKeyboardButton(button_text, callback_data=new_callback_data))
        return new_keyboard

if __name__ == "__main__":
    with open(variables.LOGGING_CONF_FILE_PATH, "r") as f:
        conf_dict = json.load(f)
    logging.config.dictConfig(conf_dict)
    try:
        server = Server()
        server.start_polling()
    except Exception as ex:
        logger = logging.getLogger("Server")
        logger.critical("Finishing the bot working due to an unexpected exception.")
        logger.exception(ex)

