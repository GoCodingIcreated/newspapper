# -*- coding: utf-8 -*-
import scrapy
import json
import sys
import os.path
import pymongo

from ..items import WebnoveItem

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from common.timestamp import current_timestamp
import common.vars as variables

class WebnovelSpider(scrapy.Spider):
    name = 'webnovel.com'

    def start_requests(self):
        client = pymongo.MongoClient(variables.MONGO_SPIDER_URL)
        books_db = client[variables.STORE_MONGO_BOOKS_DB]
        books_table = books_db[variables.STORE_MONGO_BOOKS_TABLE]
        urls = [item["book_url"] for item in books_table.find({"platform": self.name})]
        self.logger.debug("URLS: " + str(urls))
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = response.css("script").re_first(r"g_data.book = (.*);")
        self.logger.debug("Response: %s" % data)
        data = data.replace('\\"', "\\'")
        data = data.encode('unicode_escape')
        #data = data.replace("\\ ", " ")
        meta = json.loads(data)
        last_relative_modify_dttm = meta["bookInfo"]["newChapterTime"]
        yield WebnoveItem(url=response.url,
                          source_crawler=self.name,
                          name=meta["bookInfo"]["bookName"],
                          description=meta["bookInfo"]["description"],
                          last_chapter_index=meta["bookInfo"]["newChapterIndex"],
                          last_modify_dttm=last_relative_modify_dttm,
                          last_relative_modify_dttm=last_relative_modify_dttm,
                          processed_dttm=current_timestamp(),
                          inc_field=meta["bookInfo"]["newChapterIndex"]
                          )


