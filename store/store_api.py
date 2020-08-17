#!/usr/bin/python3
import pymongo
import os
import sys


sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
import common.vars as variables
from common.timestamp import current_timestamp

# TODO: Add log to logs/store/store_api.log (append)
# TODO: Add more log prints


class StoreApiException(Exception):
    pass


class StoreApi:
    def __init__(self):
        self.client = pymongo.MongoClient(variables.MONGO_URL)
        self.track_db = self.client[variables.STORE_MONGO_BOOKS_TRACK_DB]
        self.track_table = self.track_db[variables.STORE_MONGO_BOOKS_TRACK_TABLE]

        self.users_db = self.client[variables.STORE_MONGO_USERS_DB]
        self.users_table = self.users_db[variables.STORE_MONGO_USERS_TABLE]

        self.representation_db = self.client[variables.STORE_MONGO_REPRESENTATIONS_DB]
        self.representation_table = self.representation_db[variables.STORE_MONGO_REPRESENTATIONS_TABLE]

        self.book_db = self.client[variables.STORE_MONGO_BOOKS_DB]
        self.book_table = self.book_db[variables.STORE_MONGO_BOOKS_TABLE]

    def add_track_book_telegram(self, chat_id, book_url, platform):
        chat_id = str(chat_id)

        if self.representation_table.find_one({"_id": platform}) is None:
            raise StoreApiException("ERROR: platform must be one of known")
        if self.users_table.find_one({"chat_id": chat_id}) is not None:
            if self.track_table.find_one({"chat_id": chat_id, "book_url": book_url}) is None:
                self.inc_book(book_url, platform)
                self.track_table.insert_one({"chat_id": chat_id, "book_url": book_url})
            else:
                print("INFO: the book is already tracking")
        else:
            raise StoreApiException("there is no user with id: " + chat_id)

    def add_telegram_user(self, chat_id):
        chat_id = str(chat_id)
        self.users_table.replace_one({"chat_id": chat_id}, {"chat_id": chat_id}, upsert=True)

    def dec_book(self, book_info):
        book = self.book_table.find_one(book_info)
        book_id = book["_id"]
        if book is not None:
            book["count"] -= 1
            if book["count"] > 0:
                self.book_table.replace_one({"_id": book_id}, book, upsert=True)
            else:
                self.book_table.delete_one({"_id": book_id})
        else:
            raise StoreApiException("There is no book with book_info " + book_info)
        return book

    def inc_book(self, book_url, platform):
        book = self.book_table.find_one({"book_url": book_url})
        if book is not None:
            book["count"] += 1
            self.book_table.replace_one({"book_url": book_url}, book, upsert=True)
        else:
            self.book_table.insert_one({"book_url": book_url, "count": 1, "platform": platform})

    def insert_representation(self, id, format):
        self.representation_table.replace_one(
            {
                "_id": id
            },
            {
                "_id": id,
                "format": format,
                "last_update_dttm": current_timestamp()
            },
            upsert=True
        )

    def remove_track_book_telegram(self, chat_id, book_info):
        chat_id = str(chat_id)
        book = self.book_table.find_one(book_info)

        # TODO: remove return and print
        print("remove_track_book_telegram: chat_id: " + chat_id + "; book_info: " + str(book_info))
        return book

        if book is None:
            raise StoreApiException("ERROR: there is no book with info: " + book_info)
        book_url = book["book_url"]
        if self.users_table.find_one({"chat_id": chat_id}) is not None:
            if self.track_table.find_one({"chat_id": chat_id, "book_url": book_url}) is not None:
                self.dec_book(book)
                self.track_table.delete_one({"chat_id": chat_id, "book_url": book_url})
            else:
                print("INFO: the book is already not tracking")
        else:
            raise StoreApiException("ERROR: there is no user with id: " + chat_id)
        return book

    def has_user(self, user_id):
        user_id = str(user_id)
        # print(self.users_table.find_one({"chat_id": user_id}))
        return self.users_table.find_one({"chat_id": user_id}) is not None

    def get_subscriptions(self, user_id):
        user_id = str(user_id)
        books = []
        for track in self.track_table.find({"chat_id": user_id}):
            book = self.book_table.find_one({"book_url": track["book_url"]})
            books.append(book)
        return books

    def get_platforms(self):
        platforms = self.representation_table.find({"_id": {"$not": "default"}})
        return [x["_id"] for x in platforms]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: Command must be:")
        sys.exit(1)
    command = sys.argv[1]
    store_api = StoreApi()
    try:
        if command == "add_track_book_telegram":
            if len(sys.argv) < 5:
                print("ERROR: usage: store_api.py add_track_book_telegram <chat_id> <book_url> <platform>")
                sys.exit(1)
            chat_id = sys.argv[2]
            book_url = sys.argv[3]
            platform = sys.argv[4]
            store_api.add_track_book_telegram(chat_id, book_url, platform)
        elif command == "add_telegram_user":
            if len(sys.argv) < 3:
                print("ERROR: usage: store_api.py add_telegram_user <chat_id>")
                sys.exit(1)
            chat_id = sys.argv[2]
            store_api.add_telegram_user(chat_id)
        elif command == "dec_book":
            if len(sys.argv) < 3:
                print("ERROR: usage: store_api.py dec_book <book_url>")
                sys.exit(1)
            book_url = sys.argv[2]
            store_api.dec_book({"book_url": book_url})
        elif command == "inc_book":
            if len(sys.argv) < 4:
                print("ERROR: usage: store_api.py inc_book <book_url> <platform>")
                sys.exit(1)
            book_url = sys.argv[2]
            platform = sys.argv[3]
            store_api.inc_book(book_url, platform)
        elif command == "insert_representation":
            store_api.insert_representation("webnovel",
                                  "New \"_$name_\" chapters!\nModified __$last_relative_modify_dttm__.\nLatest chapter now $last_chapter_index.\nSee at [$url]($url)")
            store_api.insert_representation("author_today",
                                  "New \"_$name_\" updates!\nModified at __$last_modify_dttm__.\nLatest chapter now $last_chapter_index.\nSee at [$url]($url)")
            store_api.insert_representation("litmarket",
                                  "New \"_$name_\" pages!\nModified __$last_relative_modify_dttm__.\nLatest pages now $last_pages_number.\nSee at [$url]($url)")
            store_api.insert_representation("default",
                                  "New \"_$name_\" updates!\nModified at __$last_modify_dttm__.\nSee at [$url]($url)")
        elif command == "remove_track_book_telegram":
            if len(sys.argv) < 4:
                print("ERROR: usage: store_api.py remove_track_book_telegram <chat_id> <book_url>")
                sys.exit(1)
            chat_id = sys.argv[2]
            book_url = sys.argv[3]
            store_api.remove_track_book_telegram(chat_id, {"book_url": book_url})
        else:
            print("ERROR: Command must be: ")
            sys.exit(1)
    except StoreApiException as ex:
        print("ERROR: Error occurred during command " + command + ": " + str(ex))
        sys.exit(1)

