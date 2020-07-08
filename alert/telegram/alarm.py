#!/usr/bin/python3
import sqlite3
import subprocess
import time
import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from common.timestamp import current_timestamp

from subprocess import CalledProcessError

# TODO: change path to normal
DB_PATH = "/home/nickolas/Development/Newspapper/store/crawler_storage.db"
DB_CRAWLER_NAME = "info"
DB_ALARM_NAME = "alarm"
PAUSE_TIME_SEC = 5
CREATE_TABLE_QUERY = "CREATE TABLE if not exists alarm (url text PRIMARY KEY, name TEXT, description TEXT, last_modify_dttm TEXT, last_alarm_dttm text NOT NULL);"

# TODO maybe add when last_modify_dttm > alarm.last_alarm_dttm and last_modify_dttm > alarm.last_modify_dttm
SELECT_QUERY = "SELECT info.url, info.name, info.last_modify_dttm, info.description  from info left join alarm on info.url = alarm.url where alarm.url is null or info.last_modify_dttm > alarm.last_modify_dttm;"

UPDATE_QUERY = "INSERT OR REPLACE INTO alarm (url, name, description, last_modify_dttm, last_alarm_dttm) values(%s, %s, %s, %s, %s);"


def send_alarm(msg):
    print("DEBUG: MESSAGE: " + msg, flush=True)
    # TODO: add normal path
    subprocess.check_call("/home/nickolas/Development/Newspapper/alert/telegram/send_alarm.sh '%s'" % str(msg),
                          shell=True)


def create_table():
    cursor.execute(CREATE_TABLE_QUERY)
    connect.commit()


def select():
    return cursor.execute(SELECT_QUERY).fetchall()


def update(e):
    query = UPDATE_QUERY % (
        '"' + str(e[0]) + '"',
        '"' + str(e[1]) + '"',
        '"' + str(e[3]) + '"',
        '"' + str(e[2]) + '"',
        '"' + str(current_timestamp()) + '"'
    )
    print("DEBUG: QUERY: " + query, flush=True)
    cursor.execute(query)
    connect.commit()


print("INFO: Start at " + current_timestamp(), flush=True)
connect = sqlite3.connect(DB_PATH)
cursor = connect.cursor()

create_table()
to_alarm = select()
print("DEBUG: TO_ALARM: " + str(to_alarm), flush=True)
# sys.exit(0)
for event in to_alarm:
    try:
        send_alarm(
            "New \"_%s_\" updates!\nModified at __%s__.\nSee at [%s](%s)" % (event[1], event[2], event[0], event[0]))
        update(event)
        time.sleep(PAUSE_TIME_SEC)
    except CalledProcessError as ex:
        print("ERROR: Error during sending message " + str(ex), flush=True)

connect.close()

print("INFO: Finish at " + current_timestamp(), flush=True)