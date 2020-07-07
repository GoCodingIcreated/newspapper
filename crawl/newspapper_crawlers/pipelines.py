# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from itemadapter import ItemAdapter
import sqlite3
import logging
import json


class SqliteStorePipeline(object):
    logger = logging.getLogger("SqliteStorePipeline")
    TABLE_NAME = "info"
    DB_NAME = "../store/crawler_storage.db"
    DDL_TABLE_QUERY = "CREATE TABLE IF NOT EXISTS %s (" \
                      "url text PRIMARY KEY, " \
                      "source_crawler text NOT NULL, " \
                      "name TEXT, " \
                      "description TEXT, " \
                      "last_modify_dttm TEXT, " \
                      "processed_dttm text NOT NULL" \
                      ");" % TABLE_NAME
    INSERT_QUERY = "INSERT OR REPLACE INTO %s (" \
                   "name, " \
                   "last_modify_dttm, " \
                   "description, " \
                   "url, " \
                   "source_crawler, " \
                   "processed_dttm" \
                   ") " \
                   "VALUES(%%s, %%s, %%s, %%s, %%s, %%s" \
                   ");" % TABLE_NAME


    connect = {}

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        query = self.create_db_insert_row_query(adapter)
        cursor = self.connect[spider.name].cursor()
        cursor.execute(query)

        self.connect[spider.name].commit()
        return item

    def open_spider(self, spider):
        self.logger.debug("Opening spider " + spider.name)
        self.connect[spider.name] = sqlite3.connect(self.DB_NAME)
        cursor = self.connect[spider.name].cursor()
        self.logger.debug("DDL QUERY: " + self.DDL_TABLE_QUERY)
        cursor.execute(self.DDL_TABLE_QUERY)
        self.connect[spider.name].commit()

    def close_spider(self, spider):
        self.logger.debug("Closing spider " + spider.name)
        self.connect[spider.name].close()

    def create_db_insert_row_query(self, adapter):
        query = self.INSERT_QUERY % ('"' + adapter.get("name") + '"',
                                     '"' + adapter.get("last_modify_dttm") + '"',
                                     '"' + adapter.get("description", "NULL") + '"',
                                     '"' + adapter.get("url", "NULL") + '"',
                                     '"' + adapter.get("source_crawler", "NULL") + '"',
                                     '"' + adapter.get("processed_dttm", "NULL") + '"'
                                     )
        self.logger.debug("INSERT QUERY: " + query)
        return query


class JsonDumpPipeline(object):
    logger = logging.getLogger("JsonDumpPipeline")
    output = {}
    LOG_PATH = "../logs/"

    def process_item(self, item, spider):
        self.logger.debug("Processing item for spider " + spider.name)
        self.dump_item(item, spider)
        return item

    def open_spider(self, spider):
        self.logger.info("Opening spider " + spider.name)
        filename = self.LOG_PATH + spider.name + ".json"
        self.output[spider.name] = open(filename, "w", encoding='utf8')

    def close_spider(self, spider):
        self.logger.info("Closing spider " + spider.name)
        self.output[spider.name].close()

    def dump_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.logger.debug("Dumping item " + str(adapter.asdict()))
        json.dump(adapter.asdict(), self.output[spider.name], ensure_ascii=False, indent=4)
        self.output[spider.name].write(",\n")

