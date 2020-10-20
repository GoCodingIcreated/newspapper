import os
import sys
import re
import bs4
import logging
import logging.config
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
import common.vars as variables
import store.store_api as store_api


class ValidatorException(Exception):
    pass


class Validator:
    def __init__(self, platform):
        self.logger = logging.getLogger("Validator")
        self.logger.info(f"Creating a Validator for the platform {platform}")
        self.db = store_api.StoreApi()
        platforms = self.db.get_platforms()

        if platform["_id"] not in [p["_id"] for p in platforms]:
            raise ValidatorException(f"There is no such platform {platform}")
        self.platform = platform["_id"]

    def validate_book(self, resp):
        self.logger.info("Validating book")
        page_content = str(resp.content)

        if resp.status_code != 200:
            self.logger.info(f"Not 200 response code. Actual code is {resp.status_code}")
            return False
        validation_book_platform_regexps = self.db.get_platform_book_validation_regexps(self.platform)
        self.logger.debug(f"validating a book, platform: {self.platform},"
                          f" validation_book_platform_regexps: {validation_book_platform_regexps}")
        for regexp in validation_book_platform_regexps:
            if re.search(validation_book_platform_regexps, page_content) is None:
                self.logger.debug(f"validation a book, platform: {self.platform},"
                                  f" validation_book_platform_regexp: {regexp}, check failed")
                return False
        self.logger.debug(f"validation a book, platform: {self.platform},"
                          f" validation_book_platform_regexps: {validation_book_platform_regexps}, check succeed")
        return True

    def get_book_info(self, page_content):
        self.logger.info(f"Getting a book info, platform: {self.platform}")
        extractors = self.db.get_platform_book_info_extractors(self.platform)
        book_info = {}
        bs = bs4.BeautifulSoup
        self.logger.debug(f"extractors: {str(extractors)}")
        for ext in extractors:

            css = ext["extraction_css"]
            field_name = ext["field_name"]
            value = bs.select_one(css) # ???
            self.logger.debug(f"extractor: {ext}, field_name: {field_name}, value: {value}")
            if value is not None:
                book_info[field_name] = value
        self.logger.debug(f"book_info: {str(book_info)}")
        return book_info

    def get_platform(self):
        return self.platform


if __name__ == "__main__":
    with open(variables.LOGGING_CONF_FILE_PATH, "r") as f:
        conf_dict = json.load(f)
    logging.config.dictConfig(conf_dict)
