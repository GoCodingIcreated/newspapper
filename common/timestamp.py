import datetime

MSK_GMT_TIMEDIF = 3

def current_timestamp():
    now = datetime.datetime.now()
    formatted = now.strftime("%Y-%m-%d %H:%M:%S")
    return formatted


def convert_gmt_zero_to_msk(dttm):
    if dttm[-1] == "Z":
        try:
            new_time = datetime.datetime.strptime(dttm, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            new_time = datetime.datetime.strptime(dttm, "%Y-%m-%dT%H:%M:%SZ")
        delta = datetime.timedelta(hours=MSK_GMT_TIMEDIF)
        dttm = datetime.datetime.strftime(new_time + delta, "%Y-%m-%d %H:%M:%S")
    return dttm


