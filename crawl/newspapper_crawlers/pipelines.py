# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from itemadapter import ItemAdapter
import sqlite3
import logging
import json
import pymongo

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from common.vars import MONGO_SPIDER_URL
from common.vars import PIPELINE_MONGO_ITEM_TABLE
from common.vars import PIPELINE_MONGO_ITEM_DB
from common.vars import PIPELINE_JSON_DUMP_LOG_DIR


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

    def process_item(self, item, spider):
        self.logger.debug("Processing item for spider " + spider.name)
        self.dump_item(item, spider)
        return item

    def open_spider(self, spider):
        self.logger.info("Opening spider " + spider.name)
        filename = os.path.join(PIPELINE_JSON_DUMP_LOG_DIR, spider.name + ".json")
        mode = "w"

        # DEBUG
        #if spider.name == "webnovel" or spider.name == "litmarket":
        #    mode = "a"

        self.output[spider.name] = open(filename, mode, encoding='utf8')

    def close_spider(self, spider):
        self.logger.info("Closing spider " + spider.name)
        self.output[spider.name].close()

    def dump_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.logger.debug("Dumping item " + str(adapter.asdict()))
        json.dump(adapter.asdict(), self.output[spider.name], ensure_ascii=False, indent=4)
        self.output[spider.name].write(",\n")


class MongoPipeline(object):
    logger = logging.getLogger("MongoPipeline")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.logger.debug("Dumping item " + str(adapter.asdict()))
        d = dict(adapter.asdict())
        d["_id"] = d["url"]
        self.items.replace_one({"_id": d["_id"]}, d, upsert=True)
        return item

    def open_spider(self, spider):
        self.logger.info("Opening spider " + spider.name)
        self.client = pymongo.MongoClient(MONGO_SPIDER_URL)
        self.db = self.client[PIPELINE_MONGO_ITEM_DB]
        self.items = self.db[PIPELINE_MONGO_ITEM_TABLE]

    def close_spider(self, spider):
        self.logger.info("Closing spider " + spider.name)
        self.client.close()

