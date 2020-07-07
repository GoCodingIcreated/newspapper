#!/usr/bin/python3
import sqlite3
import subprocess
import time
import datetime


from subprocess import CalledProcessError

# TODO: change path to normal
DB_PATH = "/home/nickolas/Development/Newspapper/store/crawler_storage.db"
DB_CRAWLER_NAME = "info"
DB_ALARM_NAME = "alarm"
PAUSE_TIME_SEC = 5
CREATE_TABLE_QUERY="CREATE TABLE if not exists alarm (url text PRIMARY KEY, name TEXT, description TEXT, last_modify_dttm TEXT, last_alarm_dttm text NOT NULL);"

# TODO maybe add when last_modify_dttm > alarm.last_alarm_dttm and last_modify_dttm > alarm.last_modify_dttm
SELECT_QUERY="SELECT info.url, info.name, info.last_modify_dttm, info.description  from info left join alarm on info.url = alarm.url where alarm.url is null or info.last_modify_dttm > alarm.last_modify_dttm;"

UPDATE_QUERY="INSERT OR REPLACE INTO alarm (url, name, description, last_modify_dttm, last_alarm_dttm) values(%s, %s, %s, %s, %s);"


def current_timestamp():
    now = datetime.datetime.now()
    formatted = now.strftime("%Y-%m-%d %H:%M:%S")
    return formatted


def send_alarm(msg):
    print("MESSAGE: " + msg)
    # TODO: add normal path
    subprocess.check_call("/home/nickolas/Development/Newspapper/alert/telegram/send_alarm.sh '%s'" % str(msg), shell=True)





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
    print("QUERY: " + query)
    cursor.execute(query)
    connect.commit()

print("Start at " + current_timestamp())
connect = sqlite3.connect(DB_PATH)
cursor = connect.cursor()

create_table()
to_alarm = select()
print("TO_ALARM: " + str(to_alarm))
#sys.exit(0)
for event in to_alarm:
    try:
        send_alarm("New %s updates. Modified at %s. See at %s" % (event[1], event[2], event[0]))
        update(event)
        time.sleep(PAUSE_TIME_SEC)
    except CalledProcessError as ex:
        print("Error during sending message " + str(ex))



connect.close()

print("Finish at " + current_timestamp())