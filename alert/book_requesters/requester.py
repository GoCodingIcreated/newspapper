import requests
import logging
import logging.config
import sys
import os
import re
import json
from .validator import Validator
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
import common.vars as variables
import store.store_api as store_api


class BookRequesterException(Exception):
    pass


class BookRequester:
    def __init__(self):
        self.logger = logging.getLogger("BookRequester")
        self.logger.info("Creating the BookRequester")
        self.validators = {}
        db = store_api.StoreApi()
        platforms = db.get_platforms()
        for platform in platforms:
            self.validators[platform["_id"]] = Validator(platform)

    def request_book(self, book_url, platform=None, force_request=False):
        self.logger.info("Requesting a book")
        self.logger.debug(f"book_url: {book_url}, platform: {platform}")
        validator = self.validators.get(platform)
        db = store_api.StoreApi()
        if validator is None:
            self.logger.debug(f"book_url: {book_url}, validator is None")
            platforms = [p["_id"] for p in db.get_platforms()]
            if platform is not None:
                self.logger.debug(f"book_url: {book_url}, platform is not None")
                if platform not in platforms:
                    ex = BookRequesterException(f"book_url: {book_url}, there is no such platform {platform}")
                    self.logger.exception(ex)
                    raise ex
                validator = Validator(platform)
                self.validators[platform] = validator
            else:
                self.logger.debug(f"book_url: {book_url}, platform is None")
                for p in platforms:
                    regexp = db.get_platform_validation_regexp(p)
                    url = re.search(regexp, book_url)
                    if url is not None:
                        self.logger.debug(f"book_url: {book_url}, regexp: {regexp}, url: {url.group(0)}")
                        platform = p
                        self.logger.debug(f"book_url: {book_url}, platform {platform} is found")
                        break
                    else:
                        self.logger.debug(f"book_url: {book_url}, regexp: {regexp}, url: {url}")

                if platform is None:
                    ex = BookRequesterException(f"There is no platform for book url {book_url}")
                    self.logger.exception(ex)
                    raise ex
                validator = self.validators.get(platform)
                if validator is None:
                    validator = Validator(platform)
                    self.validators[platform] = validator
        else:
            self.logger.debug(f"book_url: {book_url}, validator is not None")
        regexp = db.get_platform_validation_regexp(platform)
        url_group = re.search(regexp, book_url)

        if url_group is None:
            self.logger.debug(f"book_url: {book_url}, platform: {platform}, regexp: {regexp}, url: {url_group}")
            self.logger.debug(f"book_url: {book_url}, url is None")
            ex = BookRequesterException(f"The URL {book_url} is not validated with validation regexp {regexp}")
            self.logger.exception(ex)
            raise ex
        url = url_group.group(0)
        self.logger.debug(f"book_url: {book_url}, platform: {platform}, regexp: {regexp}, url: {url}")
        if not force_request:
            self.logger.info("Trying to get the book from DB")
            book = db.get_book({"book_url": url})
            self.logger.debug(f"book_url: {url}, book: {book}")
            if book is not None:
                self.logger.info(f"Returning a book: {book} from DB")
                return book

        resp = requests.get(url)
        new_book_url = resp.url
        self.logger.debug(f"book_url: {book_url}, response status: {resp.status_code}, new_book_url: {new_book_url}")

        if not force_request:
            self.logger.info("Trying to get the book from DB")
            book = db.get_book({"book_url": new_book_url})
            self.logger.debug(f"book_url: {new_book_url}, book: {book}")
            if book is not None:
                self.logger.info(f"Returning a book: {book} from DB")
                return book

        if validator.validate_book(resp):
            book_info = validator.get_book_info(resp)
            book_info["book_url"] = new_book_url
            book_info["platform"] = platform
            self.logger.debug(f"book_url: {new_book_url}, book_info: {str(book_info)}")
            return book_info
        else:
            self.logger.debug(f"book_url: {new_book_url}, book_info returned from validator is None")
            return None


if __name__ == "__main__":
    with open(variables.LOGGING_CONF_FILE_PATH, "r") as f:
        conf_dict = json.load(f)
    logging.config.dictConfig(conf_dict)