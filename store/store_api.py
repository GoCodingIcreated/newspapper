#!/usr/bin/python3
import pymongo
import os
import sys
import logging
import json
import logging.config

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
import common.vars as variables
from common.timestamp import current_timestamp


class StoreApiException(Exception):
    pass


class StoreApi:
    def __init__(self):
        self.logger = logging.getLogger("StoreApi")
        self.client = pymongo.MongoClient(variables.MONGO_STORE_API_URL)

        # self.track_db = self.client[variables.STORE_MONGO_BOOKS_TRACK_DB]
        # self.track_table = self.track_db[variables.STORE_MONGO_BOOKS_TRACK_TABLE]

        self.users_db = self.client[variables.STORE_MONGO_USERS_DB]
        self.users_table = self.users_db[variables.STORE_MONGO_USERS_TABLE]

        self.representation_db = self.client[variables.STORE_MONGO_REPRESENTATIONS_DB]
        self.representation_table = self.representation_db[variables.STORE_MONGO_REPRESENTATIONS_TABLE]

        self.book_db = self.client[variables.STORE_MONGO_BOOKS_DB]
        self.book_table = self.book_db[variables.STORE_MONGO_BOOKS_TABLE]

        self.platform_book_validations_db = self.client[variables.STORE_MONGO_PLATFORM_BOOK_VALIDATIONS_DB]
        self.platform_book_validations_table = \
            self.platform_book_validations_db[variables.STORE_MONGO_PLATFORM_BOOK_VALIDATIONS_TABLE]

        self.book_info_extractors_db = self.client[variables.STORE_MONGO_PLATFORM_BOOK_INFO_EXTRACTORS_DB]
        self.book_info_extractors_table = \
            self.book_info_extractors_db[variables.STORE_MONGO_PLATFORM_BOOK_INFO_EXTRACTORS_TABLE]

        self.items_db = self.client[variables.PIPELINE_MONGO_ITEM_DB]
        self.items_table = self.items_db[variables.PIPELINE_MONGO_ITEM_TABLE]

        self.alarm_db = self.client[variables.ALARM_MONGO_ALERT_DB]
        self.alarm_table = self.alarm_db[variables.ALARM_MONGO_ALERT_TABLE]

    """
        chat_id: string\int number
        book:
            book_url (Required):
            platform (Required):
            description:
            author:
    """
    def add_track_book_telegram(self, chat_id, book):
        self.logger.debug(f"chat_id: {chat_id}, book: {str(book)}")
        chat_id = str(chat_id)
        book_rec = self.get_book(book)
        if book_rec is not None:
            self.logger.debug(f"There is the book: {book_rec} in DB for request book: {book}. Using book from DB")
            book = book_rec

        book_url = book.get("book_url")
        platform = book.get("platform")

        if book_url is None:
            ex = StoreApiException(f"book_url must be provided, chat_id: {chat_id}, book: {book}")
            self.logger.error(f"book_url must be provided, chat_id: {chat_id}, book: {book}")
            self.logger.exception(ex)
            raise ex

        if platform is None:
            ex = StoreApiException(f"platform must be provided, chat_id: {chat_id}, book: {book}")
            self.logger.error(f"platform must be provided, chat_id: {chat_id}, book: {book}")
            self.logger.exception(ex)
            raise ex

        if self.representation_table.find_one({"_id": platform}) is None:
            ex = StoreApiException(f"An unknown platform: {platform}")
            self.logger.error(f"An unknown platform: {platform}")
            self.logger.exception(ex)
            raise ex

        user = self.users_table.find_one({"chat_id": chat_id})
        if user is None:
            ex = StoreApiException(f"There is no such user with chat_id: {chat_id}")
            self.logger.error(f"There is no such user with chat_id: {chat_id}")
            self.logger.exception(ex)
            raise ex

        is_tracked = False

        if user["books"].get(book_url) is not None:
            self.logger.info(f"The book {book_url} is already tracking for the user {chat_id}")
        else:
            self.add_book(book)
            self.logger.info(f"Start tracking a book {book} for the user {chat_id}")
            user["books"][book_url] = {
                "book_url": book_url,
                "pause": False
            }
            # TODO: replace replace to update
            self.logger.debug(f"Updated user: {user}")
            self.users_table.replace_one({"chat_id": chat_id}, user)


    """
        chat_id: string\int number
        book:
            book_url (Required):
            platform (Required):
            description:
            author:
    """
    def remove_track_book_telegram(self, chat_id, book_info):
        self.logger.debug(f"chat_id: {chat_id}, book_info: {book_info}")
        chat_id = str(chat_id)
        book = self.book_table.find_one(book_info)

        self.logger.debug(f"chat_id: {chat_id}, book_info: {book_info}, book: {book}")
        if book["book_url"] is None:
            ex = StoreApiException(f"There is no such book with info: {book_info}")
            self.logger.debug(f"There is no such book with info: {book_info}")
            self.logger.exception(ex)
            raise ex
        book_url = book.get("book_url")
        if book_url is None:
            ex = StoreApiException(f"There is a book {book} in book_table without book_url")
            self.logger.critical(f"There is a book {book} in book_table without book_url")
            self.logger.exception(ex)
            raise ex

        user = self.users_table.find_one({"chat_id": chat_id})
        if user is None:
            ex = StoreApiException(f"There is no such user with chat_id: {chat_id}")
            self.logger.debug(f"There is no such user with chat_id: {chat_id}")
            self.logger.exception(ex)
            raise ex

        is_tracked = False
        if user["books"].get(book_url) is None:
            self.logger.info(f"The book {book_info} is already not tracking for the user {chat_id}")
        else:
            self.logger.info(f"Stop tracking a book {book} for the user {chat_id}")
            del user["books"][book_url]
            # TODO: replace replace to update
            self.users_table.replace_one({"chat_id": chat_id}, user)


    """
        chat_id: string\int number
        pause: True\False
        books: [   
            book_url: {
                "book_url" : book_url,
                "last_chapter": chapter,
                "last_page": page,
                "last_modify_dttm": dttm,
                "last_alert_time": dttm,
                "pause": True/False,
                "platform": platform
            }
        ]
    """
    def add_telegram_user(self, chat_id):
        self.logger.debug(f"chat_id: {chat_id}")
        chat_id = str(chat_id)
        if self.users_table.find_one({"chat_id": chat_id}) is None:
            self.logger.info(f"Adding a new user {chat_id}.")
            self.users_table.insert_one({"chat_id": chat_id, "books": {}, "pause": False})
        else:
            self.logger.info(f"The user {chat_id} is already in the DB.")

    """
        book:
            book_url (Required):
            platform (Required):
            description:
            author:
    """
    def add_book(self, book):
        self.logger.debug(f"book: {book}")
        book_url = book.get("book_url")
        platform = book.get("platform")
        if book_url is None:
            ex = StoreApiException(f"book_url must be provided. The requested book: {book}")
            self.logger.error(f"There is request {book} without a book_url")
            self.logger.exception(ex)
            raise ex
        if platform is None:
            ex = StoreApiException(f"platform must be provided. The requested book: {book}")
            self.logger.error(f"There is request {book} without a platform")
            self.logger.exception(ex)
            raise ex
        old_book = self.book_table.find_one({"book_url": book_url})
        self.logger.debug(f"Book: {book}, old_book: {old_book}")
        if old_book is not None:
            self.book_table.replace_one({"book_url": book_url}, book, upsert=True)
            self.logger.info(f"The book {book} is already added. Previous value: {old_book}. New value: {book}")
        else:
            book = self.book_table.insert_one(book)
            self.logger.info(f"The book {book} has been added.")

    """
        book:
            book_url (Required):
            platform (Required):
            description:
            author:
    """
    def remove_book(self, book):
        self.logger.debug(f"book: {book}")
        book_url = book.get("book_url")
        platform = book.get("platform")
        if book_url is None:
            ex = StoreApiException(f"book_url must be provided. Requested book: {book}")
            self.logger.error(f"There is request {book} without book_url")
            self.logger.exception(ex)
            raise ex
        if platform is None:
            ex = StoreApiException(f"platform must be provided. Requested book: {book}")
            self.logger.error(f"There is request {book} without platform")
            self.logger.exception(ex)
            raise ex
        old_book = self.book_table.find_one({"book_url": book_url})
        self.logger.debug(f"Book: {book}, old_book: {old_book}")
        if old_book is not None:
            self.book_table.delete_one({"book_url": book_url})
            self.logger.info(f"Book {book} has been removed.")
        else:
            self.logger.info(f"Can't remove book {book} because it's missed in DB")

    """       
        book: one of the param:
            book_url:
            platform:
            description:
            author:
    """
    def get_book(self, book):
        self.logger.debug(f"book: {book}")
        book_record = self.book_table.find_one(book)
        self.logger.debug(f"book: {book}, book_record: {book_record}")
        return book_record

    # TODO: add new params (validation, extractors)
    def insert_representation(self, id, format):
        self.logger.debug(f"id: {id}, format: {format}")
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

    """
        chat_id: int\string number
    """
    def has_user(self, chat_id):
        self.logger.debug(f"chat_id: {chat_id}")
        chat_id = str(chat_id)
        user = self.users_table.find_one({"chat_id": chat_id})
        self.logger.debug(f"chat_id: {chat_id}, user: {user}, user is not None: {user is not None}")
        return self.users_table.find_one({"chat_id": chat_id}) is not None

    """
        chat_id: int\string number
    """
    def get_subscriptions(self, chat_id):
        self.logger.debug(f"chat_id: {chat_id}")
        chat_id = str(chat_id)
        books = []

        tracks = self.users_table.find_one({"chat_id": chat_id})["books"]
        self.logger.debug(f"chat_id: {chat_id}, tracks: {tracks}")

        books = tracks.values()

        self.logger.debug(f"chat_id: {chat_id}, book: {books}")
        return books

    def get_platforms(self):
        self.logger.debug("Get platforms")
        platforms = list(self.representation_table.find({"_id": {"$ne": "default"}}))
        self.logger.debug(f"platforms: {platforms}")
        return platforms

    """
        author_today: r"http[s]?://author.today/work/[0-9]*"
        platform: string
    """
    def get_platform_validation_regexp(self, platform):
        self.logger.debug(f"platform: {platform}")
        record_platform = self.representation_table.find_one({"_id": platform})
        self.logger.debug(f"platform: {platform}, record_platform: {record_platform}")
        if record_platform is None:
            ex = StoreApiException(f"There is no platform {platform}")
            self.logger.error(f"There is no platform {platform}")
            self.logger.exception(ex)
            raise ex
        if record_platform.get("validation_regexp") is None:
            ex = StoreApiException(f"There is no validation_regexp for a platform {platform}, record_platform: {record_platform}")
            self.logger.error(f"There is no validation_regexp for a platform {platform}, record_platform: {record_platform}")
            self.logger.exception(ex)
            raise ex
        validation_regexp = record_platform["validation_regexp"]
        self.logger.debug(f"platform: {platform}, validation_regexp: {validation_regexp}")
        return record_platform["validation_regexp"]

    """
        validation:
            platform (required): target platform to check
            regexp (required): regexp to check if url is valid
    """
    def insert_platform_book_validation_regexp(self, validation):
        self.logger.debug(f"validation: {validation}")

        platform = validation["platform"]
        if platform is None:
            ex = StoreApiException(f"Validation {validation} must content a 'platform' field")
            self.logger.error(f"Validation {validation} must content a 'platform' field")
            self.logger.exception(ex)
            raise ex

        if self.representation_table.find_one({"_id": platform}) is None:
            ex = StoreApiException(f"There is no such platform {platform}")
            self.logger.error(f"There is no such platform {platform}")
            self.logger.exception(ex)
            raise ex
        self.platform_book_validations_table.insert_one(validation)

    """
        validation:
            platform (required): target platform to check
            regexp (required): regexp to check if url is valid        
    """
    def get_platform_book_validation_regexps(self, platform):
        self.logger.debug(f"platform: {platform}")
        if self.representation_table.find_one({"_id": platform}) is None:
            ex = StoreApiException(f"There is no such platform {platform}")
            self.logger.error(f"There is no such platform {platform}")
            self.logger.exception(ex)
            raise ex
        validation_regexps = list(self.platform_book_validations_table.find({"platform": platform}))
        self.logger.debug(f"platform: {platform}, validation_regexps: {validation_regexps}")
        return validation_regexps

    """    
        extractor:
            platform (required): target platform to extract field 
            field_name (required): name in result table for extracted field
            extraction_css (required): extraction string for bs4 selector
    """
    def insert_platform_book_info_extractor(self, extractor):
        self.logger.debug(f"extractor: {extractor}")
        if extractor.get("platform") is None:
            ex = StoreApiException(f"A field platform is absent in extraction {extractor}")
            self.logger.error(f"A field platform is absent in extraction {extractor}")
            self.logger.exception(ex)
            raise ex
        platform = extractor["platform"]
        if self.representation_table.find_one({"_id": platform}) is None:
            ex = StoreApiException(f"There is no such platform {platform}")
            self.logger.error(f"There is no such platform {platform}")
            self.logger.exception(ex)
            raise ex

        self.book_info_extractors_table.insert_one(extractor)

    """
        extractor:
            platform (required): target platform to extract field
            field_name (required): name in result table for extracted field
            extraction_css (required): extraction string for bs4 selector
    """
    def get_platform_book_info_extractors(self, platform):
        self.logger.debug(f"platform: {platform}")
        if self.representation_table.find_one({"_id": platform}) is None:
            ex = StoreApiException(f"There is no such platform {platform}")
            self.logger.error(f"There is no such platform {platform}")
            self.logger.exception(ex)
            raise ex
        extractors = list(self.book_info_extractors_table.find({"platform": platform}))
        self.logger.debug(f"platform: {platform}, extractors: {extractors}")
        return extractors

    def is_subscribed_on_book(self, chat_id, book_url):
        chat_id = str(chat_id)
        self.logger.debug(f"chat_id: {chat_id}, book_url: {book_url}")
        user = self.users_table.find_one({"chat_id": chat_id})
        return user["books"].get(book_url) is not None

        # return self.track_table.find_one({"chat_id": chat_id, "book_url": book_url}) is not None

    """
        platform (required): name of platform, string
    """
    def get_items_by_platform(self, platform):
        self.logger.debug(f"Platform: {platform}")
        return list(self.items_table.find({"source_crawler": platform}))

    """
        item
            url (required): url of the book
    """
    def get_book_by_item(self, item):
        self.logger.debug(f"item: {item}")
        url = item.get("url")
        if url is None:
            ex = StoreApiException(f"There is item without URL: {item}")
            self.logger.error(f"There is item without URL: {item}")
            self.logger.exception(f"There is item without URL: {item}")
            raise ex
        book = self.book_table.find_one({"book_url": url})
        self.logger.debug(f"item: {item}, book: {book}")
        return book

    """
        book:
            book_url (required): book URL 
    """
    def get_alert_by_book(self, book):
        self.logger.debug(f"book: {book}")
        url = book.get("book_url")
        if url is None:
            ex = StoreApiException(f"There is a book {book} without book_url")
            self.logger.error(f"There is a book {book} without book_url")
            self.logger.exception(ex)
            raise ex
        alert = self.alarm_table.find_one({"url": url})
        self.logger.debug(f"book: {book}, alert: {alert}")
        return alert

    """
        book:
            book_url (required): book URL 
    """
    """
    def get_tracks_by_book(self, book):
        self.logger.debug(f"book: {book}")
        url = book.get("book_url")
        if url is None:
            ex = StoreApiException(f"There is a book {book} without book_url")
            self.logger.error(f"There is a book {book} without book_url")
            self.logger.exception(ex)
            raise ex
        tracks = list(self.track_table.find({"book_url": url}))
        self.logger.debug(f"book: {book}, tracks: {tracks}")
        return tracks
    """

    """
            item
                url (required): url of the book
        """
    def update_user_alerts(self, user):
        self.logger.debug(f"user: {user}")
        self.users_table.replace_one({"chat_id": user["chat_id"]}, user)

    def get_users(self):
        return list(self.users_table.find())


    def get_platform_representaion(self, platform):
        self.logger.debug(f"platform: {platform}")
        return self.representation_table.find_one({"platform": platform})["format"]

    def get_item_by_book(self, book):
        self.logger.debug(f"book: {book}")
        return self.items_table.find_one({"url": book["book_url"]})

    def user_pause_alerts(self, user):
        self.logger.debug(f"user: {user}")
        # TODO: replace replace to update
        user_in_db = self.users_table.find_one({"chat_id": user["chat_id"]})
        user_in_db["pause"] = True
        self.users_table.replace_one({"chat_id": user["chat_id"]}, user_in_db)

    def user_unpause_alerts(self, user):
        self.logger.debug(f"user: {user}")
        # TODO: replace replace to update
        user_in_db = self.users_table.find_one({"chat_id": user["chat_id"]})
        user_in_db["pause"] = False
        self.users_table.replace_one({"chat_id": user["chat_id"]}, user_in_db)

    def user_pause_book(self, user, book_url):
        self.logger.debug(f"user: {user}, book_url: {book_url}")
        user_in_db = self.users_table.find_one({"chat_id": user["chat_id"]})
        if user_in_db["books"].get(book_url) is None:
            self.logger.warning("Tried to pause untracked book")
        else:
            user_in_db["books"][book_url]["pause"] = True
            self.users_table.replace_one({"chat_id": user["chat_id"]}, user_in_db)


    def user_unpause_book(self, user, book_url):
        self.logger.debug(f"user: {user}, book_url: {book_url}")
        user_in_db = self.users_table.find_one({"chat_id": user["chat_id"]})
        if user_in_db["books"].get(book_url) is None:
            self.logger.warning("Tried to unpause untracked book")
        else:
            user_in_db["books"][book_url]["pause"] = False
            self.users_table.replace_one({"chat_id": user["chat_id"]}, user_in_db)

if __name__ == "__main__":
    with open(variables.LOGGING_CONF_FILE_PATH, "r") as f:
        conf_dict = json.load(f)
    logging.config.dictConfig(conf_dict)
    store_api = StoreApi()


