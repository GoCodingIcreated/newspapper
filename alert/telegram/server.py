import pymongo
import telebot

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
import common.vars as variables


class Server:
    GET_TRACKS = "Get tracks"
    START_TRACKS = "Start tracking"
    STOP_TRACKS = "Stop tracking"
    NOT_ALLOWED = "Not allowed"
    def __init__(self):
        self.db = DbAPI()
        with open(variables.TOKEN_PATH, "r") as f:
            token = f.readline()
            print("token: " + token)
        self.bot = telebot.TeleBot(token)
        self.hello_msg = "Hello! I'm Bot for tracking new chapters on AuthorToday, Litmarket, Webnovel."

        keyboard_main = telebot.types.ReplyKeyboardMarkup()
        keyboard_main.row(Server.GET_TRACKS)
        keyboard_main.row(Server.START_TRACKS)
        keyboard_main.row(Server.STOP_TRACKS)


        @self.bot.message_handler(commands=['start'])
        def start_message(message):
            print(message.chat.id)
            if not self.has_rights(message.chat.id):
                self.bot.send_message(message.chat.id, Server.NOT_ALLOWED)
                return
            self.bot.send_message(message.chat.id, self.hello_msg, reply_markup=keyboard_main)

        @self.bot.message_handler(content_types=['text'])
        def send_text(message):
            print(message.chat.id)
            if not self.has_rights(message.chat.id):
                self.bot.send_message(message.chat.id, Server.NOT_ALLOWED)
                return

            if message.text == Server.GET_TRACKS:
                subscriptions = self.get_subscription_list(message.chat.id)
                self.bot.send_message(message.chat.id, "Subscriptions: \n" + "\n".join(subscriptions))
            elif message.text == Server.START_TRACKS:
                is_success = self.add_subscription(message.chat.id)
                self.bot.send_message(message.chat.id, 'Прощай, создатель')
            elif message.text == Server.STOP_TRACKS:
                is_success = self.remove_subscription(message.chat.id)
                self.bot.send_sticker(message.chat.id, 'CAADAgADZgkAAnlc4gmfCor5YbYYRAI')


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


class DbAPI():
    def __init__(self):
        self.db = pymongo.MongoClient(variables.MONGO_URL)

        self.users_db = self.db[variables.STORE_MONGO_USERS_DB]
        self.users_table = self.users_db[variables.STORE_MONGO_USERS_TABLE]

        self.telegram_init_db = self.db[variables.ALERT_TELEGRAM_INIT_DB]
        self.telegram_init_table = self.telegram_init_db[variables.ALERT_TELEGRAM_INIT_TABLE]

        self.tracks_db = self.db[variables.STORE_MONGO_BOOKS_TRACK_DB]
        self.tracks_table = self.tracks_db[variables.STORE_MONGO_BOOKS_TRACK_TABLE]

        self.books_db = self.db[variables.STORE_MONGO_BOOKS_DB]
        self.books_table = self.books_db[variables.STORE_MONGO_BOOKS_TABLE]

    def has_user(self, user_id):
        print(self.users_table.find_one({"chat_id": user_id}))
        return self.users_table.find_one({"chat_id": user_id}) is not None

    def get_subscriptions(self, user_id):
        books = []
        for track in self.tracks_table.find({"chat_id": user_id}):
            book = self.books_table.find_one({"book_url": track["book_url"]})
            # TODO: change to name
            # books.append(book["name"])
            books.append(book["book_url"])
        print("Books: " + str(books))
        return books

if __name__ == "__main__":
    server = Server()
