# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime, pytz

def get_datetime_as_str(dt):
    timezone = pytz.timezone("America/Sao_Paulo")
    today = pytz.utc.localize(datetime.datetime.today()).astimezone(timezone)
    dt_tz = pytz.utc.localize(dt).astimezone(timezone)

    diff = (today.date() - dt_tz.date()).days

    day_str = get_weekday_as_str(dt, timezone)
    time_str = dt_tz.strftime("%H:%M:%S")

    return time_str if diff == 0 else day_str + ' &agrave;s ' + time_str

def get_weekday_as_str(dt, timezone):
    today = pytz.utc.localize(datetime.datetime.today()).astimezone(timezone)
    dt_tz = pytz.utc.localize(dt).astimezone(timezone)

    weekday_list = ['Hoje','Ontem','Dom','Seg','Ter','Qua','Qui','Sex','S&aacute;b']
    weekday_num = int(dt_tz.strftime("%w"))

    diff = (today.date() - dt_tz.date()).days

    if diff < 7:
        weekday = weekday_list[diff if diff < 2 else weekday_num+2]
    else:
        weekday = "H&aacute; " + str(diff) + " dias"

    return weekday
