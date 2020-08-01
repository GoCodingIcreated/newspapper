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


def add_track_book_telegram(chat_id, book_url, platform):
    client = pymongo.MongoClient(variables.MONGO_URL)
    track_db = client[variables.STORE_MONGO_BOOKS_TRACK_DB]
    track_table = track_db[variables.STORE_MONGO_BOOKS_TRACK_TABLE]

    users_db = client[variables.STORE_MONGO_USERS_DB]
    users_table = users_db[variables.STORE_MONGO_USERS_TABLE]

    representation_db = client[variables.STORE_MONGO_REPRESENATIONS_DB]
    representation_table = representation_db[variables.STORE_MONGO_REPRESENATIONS_TABLE]

    if representation_table.find_one({"_id": platform}) is None:
        raise StoreApiException("ERROR: platform must be one of known")

    if users_table.find_one({"chat_id": chat_id}) is not None:
        if track_table.find_one({"chat_id": chat_id, "book_url": book_url}) is None:
            inc_book(book_url, platform)
            track_table.insert_one({"chat_id": chat_id, "book_url": book_url})
        else:
            print("INFO: the book is already tracking")
    else:
        raise StoreApiException("there is no user with id: " + chat_id)


def add_telegram_user(chat_id):
    client = pymongo.MongoClient(variables.MONGO_URL)
    users_db = client[variables.STORE_MONGO_USERS_DB]
    users_table = users_db[variables.STORE_MONGO_USERS_TABLE]
    users_table.replace_one({"chat_id": chat_id}, {"chat_id": chat_id}, upsert=True)


def dec_book(book_url):
    client = pymongo.MongoClient(variables.MONGO_URL)
    book_db = client[variables.STORE_MONGO_BOOKS_DB]
    book_table = book_db[variables.STORE_MONGO_BOOKS_TABLE]

    book = book_table.find_one({"book_url": book_url})
    if book is not None:
        book["count"] -= 1
        if book["count"] > 0:
            book_table.replace_one({"book_url": book_url}, book, upsert=True)
        else:
            book_table.delete_one({"book_url": book_url})
    else:
        raise StoreApiException("There is no book with url " + book_url)


def inc_book(book_url, platform):
    client = pymongo.MongoClient(variables.MONGO_URL)
    book_db = client[variables.STORE_MONGO_BOOKS_DB]
    book_table = book_db[variables.STORE_MONGO_BOOKS_TABLE]

    book = book_table.find_one({"book_url": book_url})
    if book is not None:
        book["count"] += 1
        book_table.replace_one({"book_url": book_url}, book, upsert=True)
    else:
        book_table.insert_one({"book_url": book_url, "count": 1, "platform": platform})


def insert_representation(id, format):
    client = pymongo.MongoClient(variables.MONGO_URL)
    db = client[variables.STORE_MONGO_REPRESENATIONS_DB]
    representation = db[variables.STORE_MONGO_REPRESENATIONS_TABLE]

    representation.replace_one(
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


def remove_track_book_telegram(chat_id, book_url):
    client = pymongo.MongoClient(variables.MONGO_URL)
    track_db = client[variables.STORE_MONGO_BOOKS_TRACK_DB]
    track_table = track_db[variables.STORE_MONGO_BOOKS_TRACK_TABLE]

    users_db = client[variables.STORE_MONGO_USERS_DB]
    users_table = users_db[variables.STORE_MONGO_USERS_TABLE]

    if users_table.find_one({"chat_id": chat_id}) is not None:
        if track_table.find_one({"chat_id": chat_id, "book_url": book_url}) is not None:
            dec_book(book_url)
            track_table.delete_one({"chat_id": chat_id, "book_url": book_url})
        else:
            print("INFO: the book is already not tracking")
    else:
        raise StoreApiException("ERROR: there is no user with id: " + chat_id)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: Command must be:")
        sys.exit(1)
    command = sys.argv[1]
    try:
        if command == "add_track_book_telegram":
            if len(sys.argv) < 5:
                print("ERROR: usage: store_api.py remove_track_book_telegram <chat_id> <book_url> <platform>")
                sys.exit(1)
            chat_id = sys.argv[2]
            book_url = sys.argv[3]
            platform = sys.argv[4]
            add_track_book_telegram(chat_id, book_url, platform)
        elif command == "add_telegram_user":
            if len(sys.argv) < 3:
                print("ERROR: usage: store_api.py remove_track_book_telegram <chat_id>")
                sys.exit(1)
            chat_id = sys.argv[2]
            add_telegram_user(chat_id)
        elif command == "dec_book":
            if len(sys.argv) < 3:
                print("ERROR: usage: store_api.py remove_track_book_telegram <book_url>")
                sys.exit(1)
            book_url = sys.argv[2]
            dec_book(book_url)
        elif command == "inc_book":
            if len(sys.argv) < 4:
                print("ERROR: usage: store_api.py remove_track_book_telegram <book_url> <platform>")
                sys.exit(1)
            book_url = sys.argv[2]
            platform = sys.argv[3]
            inc_book(book_url, platform)
        elif command == "insert_representation":
            insert_representation("webnovel",
                                  "New \"_$name_\" chapters!\nModified __$last_relative_modify_dttm__.\nLatest chapter now $last_chapter_index.\nSee at [$url]($url)")
            insert_representation("author_today",
                                  "New \"_$name_\" updates!\nModified at __$last_modify_dttm__.\nLatest chapter now $last_chapter_index.\nSee at [$url]($url)")
            insert_representation("litmarket",
                                  "New \"_$name_\" pages!\nModified __$last_relative_modify_dttm__.\nLatest pages now $last_pages_number.\nSee at [$url]($url)")
            insert_representation("default",
                                  "New \"_$name_\" updates!\nModified at __$last_modify_dttm__.\nSee at [$url]($url)")
        elif command == "remove_track_book_telegram":
            if len(sys.argv) < 4:
                print("ERROR: usage: store_api.py remove_track_book_telegram <chat_id> <book_url>")
                sys.exit(1)
            chat_id = sys.argv[2]
            book_url = sys.argv[3]
            remove_track_book_telegram(chat_id, book_url)
        else:
            print("ERROR: Command must be: ")
            sys.exit(1)
    except StoreApiException as ex:
        print("ERROR: Error occurred during command " + command + ": " + str(ex))
        sys.exit(1)

