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

import alert.telegram.alarm as alarm


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
                    self.send_message(chat_id=message.chat.id, text=Server.NOT_ALLOWED, reply_markup=remove_keyboard)
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
                    self.send_message(chat_id=message.chat.id, text=msg, reply_markup=remove_keyboard)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when started an interaction with a new user: {message.chat.id}")
                    self.logger.exception(ex)
                    self.send_message(chat_id=message.chat.id, text="Sorry, an unknown error occurred.", reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the new user: {message.chat.id}")
                self.logger.exception(ex)

        @self.bot.message_handler(commands=['list'])
        def handler_list(message):
            try:
                self.logger.debug("Got a message: " + str(message))
                if not self.has_rights(message.chat.id):
                    self.send_message(chat_id=message.chat.id, text=Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    subscriptions = self.get_subscription_list(message.chat.id)
                    # book_urls = [sub["book_url"] for sub in subscriptions]
                    # msg = "Subscriptions: \n" + "\n\n".join(book_urls)
                    msg = str(subscriptions)

                    self.send_message(chat_id=message.chat.id, text=msg,
                                          reply_markup=remove_keyboard,
                                          parse_mode="HTML",
                                          disable_web_page_preview=True)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when executed '/list' command for the user: {message.chat.id}")
                    self.logger.exception(ex)
                    self.send_message(chat_id=message.chat.id, text="Sorry, an unknown error occurred.", reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the user: {message.chat.id}")
                self.logger.exception(ex)

        @self.bot.message_handler(commands=['pause', 'unpause'])
        def handler_pause(message):
            try:
                self.logger.debug("Got a message: " + str(message))
                if not self.has_rights(message.chat.id):
                    self.send_message(chat_id=message.chat.id, text=Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    if message.text == "/pause":
                        self.db.user_pause_alerts({"chat_id": str(message.chat.id)})
                        msg = "Paused notifications for books"
                        self.send_message(chat_id=message.chat.id, text=msg, reply_markup=remove_keyboard,
                                          disable_web_page_preview=True)
                    elif message.text == "/unpause":
                        telegram_alarm = alarm.TelegramAlarm()

                        self.db.user_unpause_alerts({"chat_id": str(message.chat.id)})
                        msg = "Unpaused notifications for books"

                        self.send_message(chat_id=message.chat.id, text=msg, reply_markup=remove_keyboard,
                                          disable_web_page_preview=True)
                        telegram_alarm.process_user(self.db.get_user(str(message.chat.id)), force_notification=True)
                    else:
                        self.logger.critical(f"Unknown command: {message.text}")
                        return


                except StoreApiException as ex:
                    self.logger.error(
                        f"An exception occurred when executed '/pause' command for the user: {message.chat.id}")
                    self.logger.exception(ex)
                    self.send_message(chat_id=message.chat.id, text="Sorry, an unknown error occurred.",
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
                    self.send_message(chat_id=message.chat.id, text=Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    platforms = [p["url"] for p in self.db.get_platforms()]
                    msg = f"Available platforms: {', '.join(platforms)}"
                    self.send_message(chat_id=message.chat.id, text=msg, reply_markup=remove_keyboard)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when executed '/platforms' command for the user: {message.chat.id}")
                    self.logger.exception(ex)
                    self.send_message(chat_id=message.chat.id, text="Sorry, an unknown error occurred.", reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the user: {message.chat.id}")
                self.logger.exception(ex)

        @self.bot.message_handler(commands=['help'])
        def handler_platform(message):
            try:
                self.logger.debug("Got a message: " + str(message))
                if not self.has_rights(message.chat.id):
                    self.send_message(chat_id=message.chat.id, text=Server.NOT_ALLOWED, reply_markup=remove_keyboard)
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
                    self.send_message(chat_id=message.chat.id, text=msg, reply_markup=remove_keyboard, disable_web_page_preview=True)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when executed '/help' command for the user: {message.chat.id}")
                    self.logger.exception(ex)
                    self.send_message(chat_id=message.chat.id, text="Sorry, an unknown error occurred.",
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
                    self.bot.answer_callback_query(call.id, "")
                    self.send_message(chat_id=call.form_user.id, text=Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    data = call.data.split()
                    if len(data) != 2:
                        msg = "An unknown button was pressed."
                        self.logger.error(f"An unknown call with 'add', call: {call}")
                        self.bot.answer_callback_query(call.id, "")
                        self.send_message(chat_id=call.from_user.id, text=msg, reply_markup=remove_keyboard)
                    else:
                        book_id = data[1]
                        book = self.db.get_book({"_id": ObjectId(book_id)})
                        if not self.db.is_subscribed_on_book(call.from_user.id, book["book_url"]):
                            self.db.add_track_book_telegram(call.from_user.id, book)
                            msg = f"Start tracking the book: {book['book_url']}."
                            keyboard = self.get_revert_keyboard(call)
                            self.bot.answer_callback_query(call.id, "")
                            self.bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                                               message_id=call.message.message_id,
                                                               reply_markup=keyboard)
                            self.send_message(chat_id=call.from_user.id, text=msg, reply_markup=remove_keyboard)
                        else:
                            msg = f"Book: {book['book_url']} has been already tracked."
                            keyboard = self.get_revert_keyboard(call)
                            self.bot.answer_callback_query(call.id, "")
                            self.bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                                               message_id=call.message.message_id,
                                                               reply_markup=keyboard)
                            self.send_message(chat_id=call.from_user.id, text=msg, reply_markup=remove_keyboard)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when executed '{call.data}' callback for the user: {call.from_user.id}")
                    self.logger.exception(ex)
                    self.send_message(chat_id=call.from_user.id, text="Sorry, an unknown error occurred.", reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the user: {call.from_user.id}")
                self.logger.exception(ex)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("remove"))
        def callback_remove(call):
            try:
                self.logger.debug("Got a call: " + str(call))
                if not self.has_rights(call.from_user.id):
                    self.bot.answer_callback_query(call.id, "")
                    self.send_message(chat_id=call.form_user.id, text=Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    data = call.data.split()
                    if len(data) != 2:
                        msg = "An unknown button pressed."
                        self.logger.error(f"An unknown call with 'remove', call: {call}")
                        self.bot.answer_callback_query(call.id, "")
                        self.send_message(chat_id=call.from_user.id, text=msg, reply_markup=remove_keyboard)
                    else:
                        book_id = data[1]
                        book = self.db.get_book({"_id": ObjectId(book_id)})
                        if self.db.is_subscribed_on_book(call.from_user.id, book["book_url"]):
                            self.db.remove_track_book_telegram(call.from_user.id, book)
                            msg = f"Stopped track the book: {book['book_url']}."
                            keyboard = self.get_revert_keyboard(call)
                            self.bot.answer_callback_query(call.id, "")
                            self.bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                                               message_id=call.message.message_id,
                                                               reply_markup=keyboard)
                            self.send_message(chat_id=call.from_user.id, text=msg, reply_markup=remove_keyboard)
                        else:
                            msg = f"The book {book['book_url']} has been already not tracked."
                            keyboard = self.get_revert_keyboard(call)
                            self.bot.answer_callback_query(call.id, "")
                            self.bot.edit_message_reply_markup(chat_id=call.from_user.id,
                                                               message_id=call.message.message_id,
                                                               reply_markup=keyboard)
                            self.send_message(chat_id=call.from_user.id, text=msg, reply_markup=remove_keyboard)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when executed '{call.data}' callback from the user: {call.from_user.id}")
                    self.logger.exception(ex)
                    self.send_message(chat_id=call.from_user.id, text="Sorry, an unknown error occurred.", reply_markup=remove_keyboard)
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
                    self.send_message(chat_id=message.chat.id, text=Server.NOT_ALLOWED, reply_markup=remove_keyboard)
                    return
                try:
                    book_info = self.requester.request_book(message.text, force_request=False)
                    if book_info is None:
                        msg = f"Sorry, but the book {message.text} was not found."
                        self.send_message(chat_id=message.chat.id, text=msg, reply_markup=remove_keyboard, disable_web_page_preview=True)
                    else:
                        book_url = book_info["book_url"]
                        if self.db.is_subscribed_on_book(message.chat.id, book_url):
                            self.logger.info(f"The user {message.chat.id} asked to remove a subscription on the book {book_url}")

                            keyboard = self.get_remove_button_keyboard(book_info["_id"])
                            book_info_from_db = self.get_book_info(self.db.get_subscriptions(message.chat.id), book_url)

                            if book_info_from_db is not None:
                                msg = book_info_from_db
                            else:
                                msg = self.get_pretty_book_info(book_info)
                            self.send_message(chat_id=message.chat.id, text=msg, reply_markup=keyboard, parse_mode="HTML")
                        else:
                            self.logger.info(f"The user {message.chat.id} asked to add a subscription on the book {book_url}")
                            self.db.add_book(book_info)
                            book = self.db.get_book(book_info)
                            keyboard = self.get_add_button_keyboard(book["_id"])
                            msg = "\n".join([f"{key}: {book_info[key]}" for key in book_info.keys() if key != "_id"])
                            msg = "The book info:\n" + msg
                            self.send_message(chat_id=message.chat.id, text=msg, reply_markup=keyboard)

                except BookRequesterException as ex:
                    self.logger.info(f"A book from link {message.text} was not found by the Requester.")
                    msg = "Sorry, but the book was not found or maybe the link is not for one of the valid platform."
                    self.send_message(chat_id=message.chat.id, text=msg, reply_markup=remove_keyboard)
                except StoreApiException as ex:
                    self.logger.error(f"An exception occurred when executed 'insert_link' for the user: {message.chat.id}")
                    self.logger.exception(ex)
                    self.send_message(chat_id=message.chat.id, text="Sorry, an unknown error occurred.", reply_markup=remove_keyboard)
            except Exception as ex:
                self.logger.critical(
                    f"An exception occurred when started an interaction with the user: {message.chat.id}")
                self.logger.exception(ex)

        # self.start_polling()

    def start_polling(self):
        self.bot.polling()

    def get_pretty_book_info(self, sub):
        MAX_DESCRIPTION_LENGTH = 128

        url = ""
        if sub.get('book_url') is not None:
            url = sub['book_url'] + "\n"

        name = ""
        if sub.get('name') is not None:
            name = f"<b>Title:</b> {sub['name']}\n"

        description = ""
        if sub.get('description') is not None:
            if len(sub['description']) < MAX_DESCRIPTION_LENGTH:
                description = self.escape_characters(sub['description']) + "\n"
            else:
                description = " ".join(
                    self.escape_characters(sub['description'])[0:MAX_DESCRIPTION_LENGTH + 1].split()[0:-1]) + "...\n"

        last_update = ""
        if sub["platform"] == 'author.today' and sub.get('last_modify_dttm') is not None:
            last_update = f"<b>Last update:</b> {sub['last_modify_dttm']}\n"

        last_fetch = ""
        if sub.get('processed_dttm') is not None:
            last_fetch = f"<b>Last fetch:</b> {sub['processed_dttm']}\n"

        last_chapter_index_str = ""
        if sub.get('last_chapter_index') is not None:
            last_chapter_index_str = f"<b>Total chapters</b>: {sub['last_chapter_index']}\n"

        last_pages_number_str = ""
        if sub.get('last_pages_number') is not None:
            last_pages_number_str = f"<b>Total pages</b>: {sub['last_pages_number']}\n"

        return f"{url}{name}{last_update}{last_fetch}{last_chapter_index_str}{last_pages_number_str}{description}\n"

    def get_book_info(self, subscriptions, book_url):
        if subscriptions.get(book_url) is None:
            return None

        sub = subscriptions[book_url]
        if sub.get('description') is None\
                or sub.get('platform') is None\
                or sub.get('processed_dttm') is None\
                or sub.get('book_url') is None:
            return None

        return self.get_pretty_book_info(sub)

    def get_subscription_list(self, user_id):

        subscriptions = self.db.get_subscriptions(str(user_id))
        output = ""
        for book_url in subscriptions.keys():
            book_info = self.get_book_info(subscriptions, book_url)
            if book_info is None:
                continue
            output += book_info
        output = "<b>Subscriptions:</b>\n\n" + output

        return output

    def escape_characters(self, msg):
        characters = [
            ("&", "&amp;"),
            ("<", "&lt;"),
            (">", "&gt;"),
        ]
        for item in characters:
            msg = msg.replace(item[0], item[1])
        return msg

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

    def send_message(self, chat_id, text, **kwargs):
        bottom = 0
        top = 0
        while bottom < len(text):
            if len(text) - bottom < variables.TELEGRAM_MESSAGE_MAX_LENGTH:
                top = len(text)
                result = text[bottom:]
            else:
                top = bottom + min(variables.TELEGRAM_MESSAGE_MAX_LENGTH, len(text) - bottom)
                result = " ".join(text[bottom:top].split(" ")[0:-1])
            if len(result) == 0:
                result = text[bottom:top]

            # print(f"TOP: {top}, BOTTOM: {bottom}, text: {result}")
            bottom = bottom + len(result) + 1
            self.logger.info(f"Sending to the user {chat_id} a message: {result}")
            self.bot.send_message(chat_id=chat_id, text=result, **kwargs)

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

