import scrapy
import json
import datetime

from newspapper_crawlers.items import AuthorTodayItem


class AuthorTodaySpider(scrapy.Spider):
    name = "author_today"

    MSK_TIMEDIF = 3
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
                              # description=None,
                              last_modify_dttm=self.convert_gmt_zero_to_msk(meta_info[self.AUTHOR_TODAY_LAST_UPDATE_DTTM_FIELD]),
                              processed_dttm=self.current_timestamp())

    def current_timestamp(self):
        now = datetime.datetime.now()
        formatted = now.strftime("%Y-%m-%d %H:%M:%S")
        return formatted

    def convert_gmt_zero_to_msk(self, dttm):
        if dttm[-1] == "Z":
            new_time = datetime.datetime.strptime(dttm, "%Y-%m-%dT%H:%M:%S.%fZ")
            delta = datetime.timedelta(hours=self.MSK_TIMEDIF)
            dttm = datetime.datetime.strftime(new_time + delta, "%Y-%m-%d %H:%M:%S")
        return dttm