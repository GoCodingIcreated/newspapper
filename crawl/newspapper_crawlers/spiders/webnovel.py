# -*- coding: utf-8 -*-
import scrapy
import json
import sys
import os.path

from ..items import WebnoveItem

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from common.timestamp import current_timestamp


class WebnovelSpider(scrapy.Spider):
    name = 'webnovel'

    def start_requests(self):
        start_urls = [
            'https://www.webnovel.com/book/16709365405930105',
        ]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = response.css("script").re_first(r"g_data.book = (.*);")
        print("DATA BEFORE: " + data)
        data = data.replace("\\ ", " ")
        print("DATA AFTER: " + data)
        meta = json.loads(data)
        yield WebnoveItem(url=response.url,
                          source_crawler=self.name,
                          name=meta["bookInfo"]["bookName"],
                          description=meta["bookInfo"]["description"],
                          last_chapter_index=meta["bookInfo"]["newChapterIndex"],
                          last_modify_dttm=meta["bookInfo"]["newChapterTime"],
                          processed_dttm=current_timestamp()
                          )


