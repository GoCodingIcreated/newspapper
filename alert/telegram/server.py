import pymongo
import telebot

import sys
import os
from bson.objectid import ObjectId

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
import common.vars as variables
import store.store_api as store_api


class Server:
    GET_TRACKS = "Get tracks"
    START_TRACKS = "Start tracking"
    STOP_TRACKS = "Stop tracking"
    NOT_ALLOWED = "Not allowed"

    def __init__(self):
        self.db = store_api.StoreApi()
        with open(variables.TOKEN_PATH, "r") as f:
            token = f.readline()
            print("token: " + token)
        self.bot = telebot.TeleBot(token)
        self.hello_msg = "Hello! I'm Bot for tracking new chapters on AuthorToday, Litmarket, Webnovel."

        keyboard_main = telebot.types.ReplyKeyboardMarkup()
        keyboard_main.row(Server.GET_TRACKS)
        keyboard_main.row(Server.START_TRACKS)
        keyboard_main.row(Server.STOP_TRACKS)

        keyboard_msg = telebot.types.InlineKeyboardMarkup()
        get_button = telebot.types.InlineKeyboardButton(Server.GET_TRACKS, callback_data="get_button")
        add_button = telebot.types.InlineKeyboardButton(Server.START_TRACKS, callback_data="add_button")
        remove_button = telebot.types.InlineKeyboardButton(Server.STOP_TRACKS, callback_data="remove_button")
        keyboard_msg.row(get_button)
        keyboard_msg.row(add_button)
        keyboard_msg.row(remove_button)

        @self.bot.message_handler(commands=['start'])
        def start_message(message):
            print(message.chat.id)
            if not self.has_rights(message.chat.id):
                self.bot.send_message(message.chat.id, Server.NOT_ALLOWED)
                return
            self.bot.send_message(message.chat.id, self.hello_msg, reply_markup=keyboard_msg)

        @self.bot.message_handler(content_types=['text'])
        def send_text(message):
            print(message.chat.id)
            if not self.has_rights(message.chat.id):
                self.bot.send_message(message.chat.id, Server.NOT_ALLOWED)
                return

        @self.bot.callback_query_handler(func=lambda call: call.data == "get_button")
        def callback_get_button(call):
            print(str(call))
            subscriptions = self.get_subscription_list(call.from_user.id)
            book_urls = [sub["book_url"] for sub in subscriptions]
            self.bot.answer_callback_query(call.id, "")
            self.bot.send_message(call.from_user.id, "Subscriptions: \n" + "\n".join(book_urls), reply_markup=keyboard_msg)

        @self.bot.callback_query_handler(func=lambda call: call.data == "add_button")
        def callback_add_button(call):
            print(str(call))
            keyboard = self.get_add_keyboard()
            self.bot.answer_callback_query(call.id, "")
            self.bot.send_message(call.from_user.id, "Select platform", reply_markup=keyboard)

        @self.bot.callback_query_handler(func=lambda call: call.data == "remove_button")
        def callback_remove_button(call):
            print(str(call))
            # is_success = self.remove_subscription(call.from_user.id)
            subscriptions = self.get_subscription_list(call.from_user.id)
            keyboard = self.get_remove_keyboard(subscriptions)
            self.bot.answer_callback_query(call.id, "")
            self.bot.send_message(call.from_user.id, "Select book to stop tracking", reply_markup=keyboard)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("stop_track_button"))
        def callback_stop_track_button(call):
            print(str(call))
            data = call.data.split()
            if len(data) != 2:
                # TODO: handle bad query
                pass
            else:
                book_id = data[1]
                book = self.db.remove_track_book_telegram(call.from_user.id, {"_id": ObjectId(book_id)})
                self.bot.answer_callback_query(call.id, "")
                self.bot.send_message(call.from_user.id, "Stopped track book: " + book["book_url"], reply_markup=keyboard_msg)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("platform_button"))
        def callback_platform_button(call):
            print(call)
            data = call.data.split()
            if len(data) != 2:
                # TODO: handle wrong query
                pass
            else:
                keyboard = None
                # self.db.add_track_book_telegram(call.from_user.id, , )
                self.bot.answer_callback_query(call.id, "")
                self.bot.send_message("", reply_markup=keyboard)


        self.start_polling()

    def start_polling(self):
        self.bot.polling()

    def send_message(self, user_id, msg):
        pass

    def get_subscription_list(self, user_id):
        return self.db.get_subscriptions(str(user_id))

    def add_subscription(self, user_id):
        pass

    def remove_subscription(self, user_id):
        pass

    def has_rights(self, user_id):
        return self.db.has_user(str(user_id))

    def get_remove_keyboard(self, subscriptions):
        keyboard = telebot.types.InlineKeyboardMarkup()
        for sub in subscriptions:
            button = telebot.types.InlineKeyboardButton(sub["book_url"],
                                                        callback_data="stop_track_button " + str(sub["_id"]))
            keyboard.row(button)

        return keyboard

    def get_add_keyboard(self):
        keyboard = telebot.types.InlineKeyboardMarkup()
        platforms = self.db.get_platforms()
        for platform in platforms:
            button = telebot.types.InlineKeyboardButton(platform,
                                                        callback_data="platform_button " + str(platform))
            keyboard.row(button)

        return keyboard

if __name__ == "__main__":
    server = Server()
