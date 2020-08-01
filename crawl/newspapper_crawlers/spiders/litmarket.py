import scrapy

import json
import sys
import os
import re
from ..items import LitmarketItem
import pymongo

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from common.timestamp import current_timestamp
import common.vars as variables

class LitmarketSpider(scrapy.Spider):
    name = 'litmarket'


    def start_requests(self):

        client = pymongo.MongoClient(variables.MONGO_URL)
        books_db = client[variables.STORE_MONGO_BOOKS_DB]
        books_table = books_db[variables.STORE_MONGO_BOOKS_TABLE]
        urls = [item["book_url"] for item in books_table.find({"platform": self.name})]
        self.logger.debug("URLS: " + str(urls))

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        name = response.css("h1.card-title::text").get()
        description = response.css("div.card-description::text").get()
        # last chapter: NOPE
        last_pages_number = response.css("div.card-bar div")[2].css("span::text").get().split()[0]
        last_relative_modify_dttm = response.css("span.date")[1].css("time::text").get()

        self.logger.debug("Response: name: %s, description: %s, last_pages_count: %s, last_relative_update: %s" %
                          (name, description, last_pages_number, last_relative_modify_dttm))
        processed_dttm = current_timestamp()
        self.logger.debug("Processed_dttm: %s" % (processed_dttm))
        last_modify_dttm = self.convert_litmarket_last_update_dttm_to_absolute(processed_dttm, last_relative_modify_dttm)
        yield LitmarketItem(url=response.url,
                            source_crawler=self.name,
                            name=name,
                            description=description,
                            last_modify_dttm=last_modify_dttm,
                            last_relative_modify_dttm=last_relative_modify_dttm,
                            last_pages_number=last_pages_number,
                            processed_dttm=processed_dttm,
                            inc_field=last_pages_number
                            )

    def convert_litmarket_last_update_dttm_to_absolute(self, current_ts, dttm):
        if re.search(r"[0-9][0-9]\.[0-9][0-9]\.[0-9][0-9]", dttm) is not None:
            # TODO: Change format
            return dttm
        # TODO: FIX IT
        return "2020-01-01 00:00:00"
        # number = dttm.split()[0]
        # quantity = dttm.split()[1]
