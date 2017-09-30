#!/usr/bin/env python3

import sys, os, argparse
from typing import List, Tuple, Dict, Any
import db

gpx_header = '''<?xml version="1.0" encoding="UTF-8" ?>
<gpx version="1.1"
 creator="DB Scripts"
 xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd" 
 xmlns="http://www.topografix.com/GPX/1/1"
 xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
 xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<trk>
<name>{}</name>
<desc>{}</desc>
<trkseg>
'''

gpx_footer = '</trkseg></trk></gpx>'

def isRoutePresent(time, duration):
    locations = db.fetchall("SELECT * from location WHERE time>=? and time<=? LIMIT 1", (time, time+duration))
    return True if locations else False

def list_workouts(with_routes):
    c = db.conn.cursor()
    rows = c.execute("SELECT time,tz,duration,type,source,distance FROM workout ORDER BY time")
    print('Time,Type,Source,Duration [mins],Distance [m]')
    for r in rows:
        (time,tz,duration,atype,source,distance) = r
        if with_routes and not isRoutePresent(time, duration):
            continue
        timestr = db.unix2datestr(time, tz, True)
        duration /= 60  # in minutes
        print('{0},{2},{3},{1:.0f},{4}'.format(timestr,duration,atype,source,distance))
    c.close()

def merger_generator(l1, l2):
    ''' Given two lists of tuples, where first element of each tuple is an increasing time,
        merge the two. I'm sure it can be done direcly in SQL...'''
    k1 = 0; k2 = 0

def gpx_point(timestr, lat, lon, alt, hr):
    ' timestr: ISO8601 UTC string '
    ext = ''
    if hr:
        ext = '<extensions><gpxtpx:TrackPointExtension><gpxtpx:hr>{}</gpxtpx:hr></gpxtpx:TrackPointExtension>'.format(hr)
    return '<trkpt lat="{:.5f}" lon="{:.5f}"><ele>{:.2f}</ele><time>{}</time>{}</trkpt>'.format(
        lat, lon, alt,
        timestr,
        ext)

def gpx_export(dateStr):
    time = db.datestr2unix(dateStr)
    if len(time) < 2:
        print('Please provide a full date with timezone, as given by the list command', file=sys.stderr)
        return
    dateStr = db.unix2datestr(time[0], time[1])  # normalize
    workouts = db.fetchall("SELECT duration,type,source,distance,name,notes FROM workout WHERE time={}".format(time[0]))
    if not workouts:
        print("Workout not found at specified time {}".format(dateStr))
        return
    (duration,atype,source,distance,name,notes) = workouts[0]
    if not name: name = '{}, recorded by {}'.format(atype, source)
    if not notes: notes = ''

    locations = db.fetchall("SELECT * from location WHERE time>=? and time<=? ORDER BY time", (time[0], time[0]+duration))
    if not locations:
        print("No route information")
        return
    metrics   = db.fetchall("SELECT * from metric WHERE time>=? and time<=? ORDER BY time", (time[0], time[0]+duration))

    f = open('{}_{}.gpx'.format(dateStr, atype), 'w')
    f.write(gpx_header.format(name, notes))
    for a in locations:
        (time, tz, lat, lon, alt) = a
        timestr = db.unix2datestr(time, 0)  # Use UTC
        f.write(gpx_point(timestr, lat * db.db2deg, lon * db.db2deg, alt/100, 0)+'\n')
    f.write(gpx_footer)
    f.close()

p = argparse.ArgumentParser(description='Workouts viewer and exporter')
p.add_argument('-l', '--list', action='store_true', help='List workouts in CSV format')
p.add_argument('--withroute', action='store_true', help='Filter workout list only for workouts with route')
p.add_argument('--gpx', type=str, help='Export GPX given starting time')
p.add_argument('--db', type=str, default='activity.db', help='database file name')
args = p.parse_args()

db.connect(args.db)

if args.list:
    list_workouts(args.withroute)
elif args.gpx:
    gpx_export(args.gpx)
else: print('{} -h for help'.format(sys.argv[0]))

db.close()
