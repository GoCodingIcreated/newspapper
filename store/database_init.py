#!/usr/bin/python3

from store_api import StoreApi

if __name__ == "__main__":
    api = StoreApi()

    # Inserting book page validation regexps
    api.insert_platform_book_validation_regexp({
        'platform': 'litmarket.ru',
        'regexp': 'div class="book-page"',
    })

    # Inserting representations.