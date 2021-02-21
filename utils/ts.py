import datetime
import time


def now_ts():
    return int(round(datetime.datetime.now().timestamp()))


def ts2str(ts, format='%Y-%m-%d %H:%M:%S'):
    return time.strftime(format, time.localtime(ts))


def str2ts(s, format='%Y-%m-%d %H:%M:%S'):
    return int(time.mktime(time.strptime(s, format)))
