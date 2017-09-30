#!/usr/bin/env python3

'''
Operations on the activity.db sqlite database.

In the SQL tables:
*  time is unix (posix) time
*  tz is the UTC offset in minutes
*  lat, lon coordinates are given in angle_degrees/180*(2**31)
*  alt (altitude) is in [cm]
*  duration in [seconds]
'''
# TODO: UTC offset to workouts

import sys, sqlite3, dateutil.parser, datetime, dateutil.tz
from typing import List, Tuple, Dict, Union, Any

METRIC_HR        = 1  # heart rate
METRIC_WEIGHT    = 2
METRIC_HEIGHT    = 3
METRIC_STEPCOUNT = 4
METRIC_FLIGHTSCLIMBED = 5
METRIC_WORKOUT_PAUSE_EVENT = 6
METRIC_WORKOUT_RESUME_EVENT = 7
METRIC_TEMPERATURE = 8
METRIC_HUMIDITY = 9
METRIC_WINDSPEED = 10
METRIC_WINDDIRECTION = 11

metrics = ['', 'hr', 'weight', 'height', 'stepcount', 'flightsclimbed']

# database <--> lat/lon degrees
db2deg = 180.0 / 2**31
deg2db = 2**31 / 180.0

create_db = '''
CREATE TABLE me (
    birthdate INT NOT NULL,
    isfemale INT
);


CREATE TABLE location (
    time INT NOT NULL,
    tz   INT NOT NULL,
    lat  INT NOT NULL,
    lon  INT NOT NULL,
    alt  INT NOT NULL,
    UNIQUE(time)
);

CREATE TABLE metric (
    time     INT NOT NULL,
    tz       INT NOT NULL,
    type     INT NOT NULL,
    duration INT NOT NULL,
    value    INT NOT NULL,
    UNIQUE(time, type)
);

CREATE TABLE workout (
    time      INT NOT NULL,
    tz        INT NOT NULL,
    duration  INT NOT NULL,
    type      TEXT NOT NULL,
    source    TEXT NOT NULL,
    distance  INT,
    name      TEXT,
    notes     TEXT,
    UNIQUE(time));
'''

conn = None  # type: sqlite3.Connection

# Insertions cursor
cursor = None  # type: sqlite3.Cursor

def connect(filename = 'activity.db'):
    ' Return true if a new database has been created '
    global conn
    conn = sqlite3.connect('activity.db')
    c = conn.cursor()
    try:
        for create in create_db.split('\n\n'):
            c.execute(create)
    except sqlite3.OperationalError:
        return False
    return True

    conn.commit()

def close():
    conn.close()

def start_insertions():
    global cursor
    cursor = conn.cursor()

def commit_insertions():
    conn.commit()

def insert_metric(time, tz, metrictype, value,duration=0):
    # type: (int, int, int, int, int) -> None
    global cursor
    cursor.execute('INSERT OR IGNORE INTO metric(time,tz,type,duration,value) VALUES(?,?,?,?,?);', (time, tz, metrictype, value, duration))

def insert_location(time, tz, lat, lon, alt):
    # type: (int, int, int, int, int) -> None
    '''
    (lat, lon): in int(degrees / 180.0 * 2**31)
    alt: in [cm]
    '''
    global cursor
    cursor.execute('INSERT OR IGNORE INTO location(time,tz,lat,lon,alt) VALUES(?,?,?,?,?);', (time, tz, lat, lon, alt))

def set_me(birthdate, isFemale):
    global cursor
    cursor.execute('INSERT OR IGNORE INTO me(birthdate,isfemale) VALUES(?,?);', (birthdate,isFemale))

def insert_by_dict(table, d):
    global cursor
    keys = d.keys()
    keys_str = ','.join(keys)
    question_marks = ','.join(['?' for k in keys])
    values = tuple([d[k] for k in keys])
    sql = 'INSERT OR IGNORE INTO {}({}) VALUES({});'.format(table, keys_str, question_marks)
    cursor.execute(sql, values)

def fetchall(query, params=()):
    c = conn.cursor()
    r = c.execute(query, params).fetchall()
    c.close()
    return r

def datestr2unix(dateStr):
    # type: (str) -> Union[Tuple[int, int], Tuple[int]]
    ' Returns (unixtime, utcoffset_minutes)'
    d = dateutil.parser.parse(dateStr)
    unixtime = int(d.timestamp())
    utcobj = d.utcoffset()
    if utcobj:
        utcoffset = int(d.utcoffset().seconds / 60)
        return (unixtime, utcoffset)
    else:
        return (unixtime,)

def unix2datestr(unixtime, utcoffset_minutes, with_tz = True):
    tz = dateutil.tz.tzoffset(None, utcoffset_minutes * 60)
    d = datetime.datetime.fromtimestamp(unixtime, tz)
    return d.strftime('%Y-%m-%dT%H:%M:%S%z') if with_tz else d.strftime('%Y-%m-%dT%H:%M:%S')




if __name__ == '__main__':
    ' A small test '
    isNew = connect()
    if not isNew:
        print('Database already exists')
        sys.exit(0)
    start_insertions()
    insert_metric(5, 0, METRIC_HR, 120)
    insert_metric(5, 0, METRIC_HR, 140)
    insert_metric(5, 0, 2, 44)
    insert_location(5, 0, 55,66,77)
    insert_by_dict('workout', {'time': 3, 'duration': 4, 'type': 'Running', 'source': 'Strava'})
    commit_insertions()
    close()
