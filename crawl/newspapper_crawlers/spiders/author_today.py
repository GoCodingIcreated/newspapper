import scrapy
import pymongo
import json
import datetime

from ..items import AuthorTodayItem
import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from common.timestamp import current_timestamp
from common.timestamp import convert_gmt_zero_to_msk
import common.vars as variables

class AuthorTodaySpider(scrapy.Spider):
    name = "author.today"


    AUTHOR_TODAY_META_CSS_PATH = "div.panel-body script::text"
    AUTHOR_TODAY_META_CSS_PATH_LIST_NUM = 0
    AUTHOR_TODAY_NAME_FIELD = "name"
    AUTHOR_TODAY_LAST_UPDATE_DTTM_FIELD = "dateModified"

    connect = None
    def start_requests(self):

        client = pymongo.MongoClient(variables.MONGO_SPIDER_URL)
        books_db = client[variables.STORE_MONGO_BOOKS_DB]
        books_table = books_db[variables.STORE_MONGO_BOOKS_TABLE]
        urls = [item["book_url"] for item in books_table.find({"platform": self.name})]
        self.logger.debug("URLS: " + str(urls))

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = response.url.split("/")[-2]
        s = response.css(self.AUTHOR_TODAY_META_CSS_PATH)[self.AUTHOR_TODAY_META_CSS_PATH_LIST_NUM].get()

        ### TODO: add somehow chapter tracking @data-time field
        # for resp in response.css("ul.list-unstyled")[2].css("li"):
        # print(resp.css("span.hint-top-right").xpath("@data-time").get())
        # print(resp.css("a::text").get())
        # print("---")
        chapters_count = len(response.css("ul.list-unstyled.table-of-content li"))
        self.logger.debug("Response: %s" % s)
        meta_info = json.loads(s)
        yield AuthorTodayItem(url=response.url,
                              source_crawler=self.name,
                              name=meta_info[self.AUTHOR_TODAY_NAME_FIELD],
                              description=meta_info["description"],
                              last_modify_dttm=convert_gmt_zero_to_msk(meta_info[self.AUTHOR_TODAY_LAST_UPDATE_DTTM_FIELD]),
                              processed_dttm=current_timestamp(),
                              last_chapter_index=chapters_count,
                              inc_field=convert_gmt_zero_to_msk(meta_info[self.AUTHOR_TODAY_LAST_UPDATE_DTTM_FIELD])
                              )



