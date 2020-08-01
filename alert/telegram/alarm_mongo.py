#!/usr/bin/python3
import pymongo
import subprocess
import time
import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from common.timestamp import current_timestamp
import common.vars as variables

from subprocess import CalledProcessError


def send_alarm(msg):
    print("DEBUG: MESSAGE: " + msg, flush=True)
    # TODO: add normal path
    subprocess.check_call("/home/nickolas/Development/Newspapper/alert/telegram/send_alarm.sh '%s'" % str(msg),
                          shell=True)


def parse(item, format):
    for key in item.keys():
        format = format.replace("$" + key, str(item[key]))
    print("DEBUG parse result: " + format, flush=True)
    return format


def update(item):
    alert_table.replace_one({"_id": item["url"]}, item, upsert=True)

print("INFO: Start at " + current_timestamp(), flush=True)
connect = pymongo.MongoClient(variables.MONGO_URL)
alert_db = connect[variables.ALARM_MONGO_ALERT_DB]
alert_table = alert_db[variables.ALARM_MONGO_ALERT_TABLE]

pipeline_db = connect[variables.PIPELINE_MONGO_ITEM_DB]
pipeline_table = pipeline_db[variables.PIPELINE_MONGO_ITEM_TABLE]

represent_db = connect[variables.STORE_MONGO_REPRESENATIONS_DB]
represent_table = represent_db[variables.STORE_MONGO_REPRESENATIONS_TABLE]

representations = represent_table.find()

for repres in representations:
    print("DEBUG repres: " + str(repres))
    for item in pipeline_table.find({"source_crawler": repres["_id"] }):
        print("DEBUG item: " + str(item))
        alert = alert_table.find_one({"url": item["url"]})
        print("DEBUG alert: " + str(alert))
        if alert is None or alert["inc_field"] < item["inc_field"]:
            print("DEBUG condition true")
            retry = 0
            while (retry < variables.ALARM_TELEGRAM_RETRIES):
                retry += 1
                try:
                    send_alarm(parse(item, repres["format"]))
                    update(item)
                    retry = variables.ALARM_TELEGRAM_RETRIES
                    time.sleep(variables.ALARM_TELEGRAM_PAUSE_ALERT_TIME_SEC)
                except CalledProcessError as ex:
                    print("ERROR: Error during sending message " + str(ex), flush=True)
                    print("INFO: Retry number: " + str(retry))


print("INFO: Finish at " + current_timestamp(), flush=True)