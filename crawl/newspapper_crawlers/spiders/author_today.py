import scrapy
import json
import datetime

from ..items import AuthorTodayItem
import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from common.timestamp import current_timestamp
from common.timestamp import convert_gmt_zero_to_msk

class AuthorTodaySpider(scrapy.Spider):
    name = "author_today"


    AUTHOR_TODAY_META_CSS_PATH = "div.panel-body script::text"
    AUTHOR_TODAY_META_CSS_PATH_LIST_NUM = 0
    AUTHOR_TODAY_NAME_FIELD = "name"
    AUTHOR_TODAY_LAST_UPDATE_DTTM_FIELD = "dateModified"

    connect = None
    def start_requests(self):
        urls = [
            'https://author.today/work/58624', # Moved by wind
            'https://author.today/work/68112', # The last from Blau
            'https://author.today/work/60081', # The Deal of Dark Mage
            'https://author.today/work/59512', # Class neutral
        ]

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

        self.logger.debug("Response: %s" % s)
        meta_info = json.loads(s)
        yield AuthorTodayItem(url=response.url,
                              source_crawler=self.name,
                              name=meta_info[self.AUTHOR_TODAY_NAME_FIELD],
                              description=meta_info["description"],
                              last_modify_dttm=convert_gmt_zero_to_msk(meta_info[self.AUTHOR_TODAY_LAST_UPDATE_DTTM_FIELD]),
                              processed_dttm=current_timestamp())



