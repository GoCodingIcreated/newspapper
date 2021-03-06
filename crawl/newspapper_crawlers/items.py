# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TutorialItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class StoreItem(scrapy.Item):
    inc_field = scrapy.Field()
    source_crawler = scrapy.Field()
    url = scrapy.Field()
    name = scrapy.Field()
    description = scrapy.Field()
    last_modify_dttm = scrapy.Field()
    processed_dttm = scrapy.Field()


class AuthorTodayItem(StoreItem):
    last_chapter_index = scrapy.Field()


class WebnoveItem(StoreItem):
    last_relative_modify_dttm = scrapy.Field()
    last_chapter_index = scrapy.Field()


class LitmarketItem(StoreItem):
    last_relative_modify_dttm = scrapy.Field()
    last_pages_number = scrapy.Field()