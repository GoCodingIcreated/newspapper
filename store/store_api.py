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
        self.client = pymongo.MongoClient(variables.MONGO_URL)

        self.track_db = self.client[variables.STORE_MONGO_BOOKS_TRACK_DB]
        self.track_table = self.track_db[variables.STORE_MONGO_BOOKS_TRACK_TABLE]

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
            ex = StoreApiException(f"Unknown platform: {platform}")
            self.logger.error(f"Unknown platform: {platform}")
            self.logger.exception(ex)
            raise ex

        if self.users_table.find_one({"chat_id": chat_id}) is not None:
            if self.track_table.find_one({"chat_id": chat_id, "book_url": book_url}) is None:
                self.add_book(book)
                self.logger.info(f"Start tracking book {book} for user {chat_id}")
                self.track_table.insert_one({"chat_id": chat_id, "book_url": book_url})
            else:
                self.logger.info(f"The book {book_url} is already tracking for user {chat_id}")
        else:
            ex = StoreApiException(f"There is no user with chat_id: {chat_id}")
            self.logger.error(f"There is no user with chat_id: {chat_id}")
            self.logger.exception(ex)
            raise ex

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
        if book is None:
            ex = StoreApiException(f"There is no book with info: {book_info}")
            self.logger.debug(f"There is no book with info: {book_info}")
            self.logger.exception(ex)
            raise ex
        book_url = book.get("book_url")
        if book_url is None:
            ex = StoreApiException(f"There is book {book} in book_table without book_url")
            self.logger.critical(f"There is book {book} in book_table without book_url")
            self.logger.exception(ex)
            raise ex

        if self.users_table.find_one({"chat_id": chat_id}) is not None:
            if self.track_table.find_one({"chat_id": chat_id, "book_url": book_url}) is not None:
                self.track_table.delete_one({"chat_id": chat_id, "book_url": book_url})
            else:
                self.logger.info(f"Book {book_info} is already not tracking for user {chat_id}")
        else:
            ex = StoreApiException(f"There is no user with chat_id: {chat_id}")
            self.logger.debug(f"There is no user with chat_id: {chat_id}")
            self.logger.exception(ex)
            raise ex

    """
        chat_id: string\int number
    """
    def add_telegram_user(self, chat_id):
        self.logger.debug(f"chat_id: {chat_id}")
        chat_id = str(chat_id)
        self.users_table.replace_one({"chat_id": chat_id}, {"chat_id": chat_id}, upsert=True)

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
            self.book_table.replace_one({"book_url": book_url}, book, upsert=True)
            self.logger.info(f"Book {book} is already added. Previous value: {old_book}. New value: {book}")
        else:
            book = self.book_table.insert_one(book)
            self.logger.info(f"Book {book} has been added.")

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
        tracks = list(self.track_table.find({"chat_id": chat_id}))
        self.logger.debug(f"chat_id: {chat_id}, tracks: {tracks}")
        for track in tracks:
            book = self.book_table.find_one({"book_url": track["book_url"]})
            books.append(book)
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
            ex = StoreApiException(f"There is no validation_regexp for platform {platform}, record_platform: {record_platform}")
            self.logger.error(f"There is no validation_regexp for platform {platform}, record_platform: {record_platform}")
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
            ex = StoreApiException(f"Validation {validation} must content 'platform' field")
            self.logger.error(f"Validation {validation} must content 'platform' field")
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
            ex = StoreApiException(f"There is no platform {platform}")
            self.logger.error(f"There is no platform {platform}")
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
    def insert_platform_book_info_extraction(self, extractor):
        self.logger.debug(f"extractor: {extractor}")
        if extractor.get("platform") is None:
            ex = StoreApiException(f"Field platform is absent in extraction {extractor}")
            self.logger.error(f"Field platform is absent in extraction {extractor}")
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
        return self.track_table.find_one({"chat_id": chat_id, "book_url": book_url}) is not None

if __name__ == "__main__":
    with open(variables.LOGGING_CONF_FILE_PATH, "r") as f:
        conf_dict = json.load(f)
    logging.config.dictConfig(conf_dict)
    store_api = StoreApi()


