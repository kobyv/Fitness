#!/usr/bin/env python3

import os, zipfile, datetime, dateutil.parser, json
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict, Any, IO

outdir = 'data'

'''Examples:
<HealthData locale="en_IL">
 <ExportDate value="2017-09-21 09:53:38 +0300"/>
 <Me HKCharacteristicTypeIdentifierDateOfBirth="1972-07-24" HKCharacteristicTypeIdentifierBiologicalSex="HKBiologicalSexMale" HKCharacteristicTypeIdentifierBloodType="HKBloodTypeOPositive" HKCharacteristicTypeIdentifierFitzpatrickSkinType="HKFitzpatrickSkinTypeNotSet"/>
 <Record type="HKQuantityTypeIdentifierHeight" sourceName="Health" sourceVersion="10.1.1" unit="cm" creationDate="2016-11-27 23:51:18 +0300" startDate="2016-11-27 23:51:18 +0300" endDate="2016-11-27 23:51:18 +0300" value="175"/>
 <Record type="HKQuantityTypeIdentifierBodyMass" sourceName="Health" sourceVersion="10.1.1" unit="kg" creationDate="2016-11-27 23:51:18 +0300" startDate="2016-11-27 23:51:18 +0300" endDate="2016-11-27 23:51:18 +0300" value="62.5"/>
 <Record type="HKQuantityTypeIdentifierHeartRate" sourceName="Koby’s Apple Watch" sourceVersion="3.1.3" device="&lt;&lt;HKDevice: 0x1c469e230&gt;, name:Apple Watch, manufacturer:Apple, model:Watch, hardware:Watch1,2, software:3.1.3&gt;" unit="count/min" creationDate="2017-02-03 09:51:27 +0300" startDate="2017-02-03 09:51:27 +0300" endDate="2017-02-03 09:51:27 +0300" value="83"/>
 <Record type="HKQuantityTypeIdentifierStepCount" sourceName="Koby’s Apple Watch" sourceVersion="3.1.3" device="&lt;&lt;HKDevice: 0x1c0685640&gt;, name:Apple Watch, manufacturer:Apple, model:Watch, hardware:Watch1,2, software:3.1.3&gt;" unit="count" creationDate="2017-02-12 09:56:36 +0300" startDate="2017-02-12 09:47:14 +0300" endDate="2017-02-12 09:48:33 +0300" value="28"/>
 <Record type="HKQuantityTypeIdentifierFlightsClimbed" sourceName="Serendipity7" sourceVersion="10.2" device="&lt;&lt;HKDevice: 0x1c4283fc0&gt;, name:iPhone, manufacturer:Apple, model:iPhone, hardware:iPhone9,4, software:10.2&gt;" unit="count" creationDate="2017-01-02 22:48:35 +0300" startDate="2017-01-02 22:15:50 +0300" endDate="2017-01-02 22:15:50 +0300" value="1"/>
 <Workout...
'''

def datestr2unix(dateStr: str) -> Tuple[int, str]:
    ' Returns (unixtime, iso in UTC) '
    d = dateutil.parser.parse(dateStr)
    u = d.utctimetuple()
    utcStr = f"{u.tm_year}-{u.tm_mon}-{u.tm_mday}T{u.tm_hour}:{u.tm_min}:{u.tm_sec}"
    unixtime = int(d.timestamp())
    return (unixtime, utcStr)
    #utcobj = d.utcoffset()
    #if utcobj:
    #    utcoffset = int(d.utcoffset().seconds / 60)
    #    return (unixtime, utcoffset)
    #else:
    #    return (unixtime,)


fileList: Dict[str, IO] = {}
f_geo = open(f"{outdir}/location.csv", 'w')
print('"Time","Lat","Lon","Alt","HorAccuracy","VerAccuracy"', file=f_geo)
f_workout = open(f"{outdir}/workout.csv", 'w')
print('"Time","Duration","Type","Distance","Source"', file=f_workout)
f_weather = open(f"{outdir}/weather.csv", 'w')
print('"Time","Temperature","Humidity"', file=f_weather)
f_tz = open(f"{outdir}/timezone.csv", 'w')
print('"Time","TZ"', file=f_tz)

def processRecord(c: ET.Element) -> None:
    t = c.attrib['type']
    isCategory = False
    if t.startswith('HKQuantityTypeIdentifier'):  # can also be HKCategoryTypeIdentifier
        t = t[len('HKQuantityTypeIdentifier'):]
    elif t.startswith('HKCategoryTypeIdentifier'):
        t = t[len('HKCategoryTypeIdentifier'):]
        isCategory = True
    else:
        return
    if not isCategory:
        unit = c.attrib.get('unit','').replace('/',':')
    dateStr  = c.attrib['startDate']
    (starttime, dateUtc) = datestr2unix(dateStr)
    (endtime, endUtc)  = datestr2unix(c.attrib['endDate']) # endUtc not used
    delta    = endtime - starttime
    value    = c.attrib.get('value', '@')
    if value == '@': return
    value = value.replace('AppleStandHourIdle', '0').replace('AppleStandHourStood', '1')

    if value.startswith('HKCategoryValue'):
        value = value[15:]

    fname = f"{outdir}/{t}.csv" if isCategory else f"data/{t}.{unit}.csv"
    if not fname in fileList:
        f = open(fname, 'w')
        print('"Time","Duration","Value"', file=f)
        fileList[fname] = f
    print(f'"{dateUtc}",{delta},"{value}"', file=fileList[fname])

'''
Example Workout:
<Workout workoutActivityType="HKWorkoutActivityTypeCycling" duration="23.56276136636734" durationUnit="min" totalDistance="4.690861185646896" totalDistanceUnit="km" totalEnergyBurned="76.76699999999995" totalEnergyBurnedUnit="kcal" sourceName="Koby’s Apple Watch" sourceVersion="3.1.3" creationDate="2017-02-07 09:41:56 +0300" startDate="2017-02-07 09:14:36 +0300" endDate="2017-02-07 09:41:41 +0300">
  <MetadataEntry key="HKTimeZone" value="Asia/Jerusalem"/>
  <MetadataEntry key="HKWeatherTemperature" value="54 degF"/>
  <MetadataEntry key="HKWeatherHumidity" value="56 %"/>
  <WorkoutEvent type="HKWorkoutEventTypePause" date="2017-02-07 09:18:29 +0300"/>
  <WorkoutEvent type="HKWorkoutEventTypeResume" date="2017-02-07 09:21:52 +0300"/>
  <WorkoutEvent type="HKWorkoutEventTypePause" date="2017-02-07 09:41:33 +0300"/>
  <WorkoutRoute sourceName="Serendipity7" sourceVersion="10.2.1" creationDate="2017-02-07 09:48:30 +0300" startDate="2017-02-07 09:14:52 +0300" endDate="2017-02-07 09:41:19 +0300">
   <Location date="2017-02-07 09:14:52 +0300" latitude="32.9876" longitude="34.8765" altitude="77.6543" horizontalAccuracy="7.21759" verticalAccuracy="5.27443" course="-1" speed="1.95025"/>
   ...
  </WorkoutRoute>
 </Workout>

'''

db2deg = 180.0 / 2**31
deg2db = 2**31 / 180.0

def processWorkoutRoute(xml_elem: ET.Element) -> None:
    for c in xml_elem:
        if c.tag != 'Location': continue
        time = datestr2unix(c.attrib['date'])
        lat = c.attrib['latitude']
        lon = c.attrib['longitude']
        alt = c.attrib['altitude']
        hacc = c.attrib['horizontalAccuracy']
        vacc = c.attrib['verticalAccuracy']
        print(f'"{time[1]}","{lat}","{lon}","{alt}","{hacc}","{vacc}"', file=f_geo)

distanceScaling = {'km': 1000, 'm':1, 'unknown':0}

def processWorkout(c):
    # type: (ET.Element) -> None
    t = c.attrib['workoutActivityType']
    if not t.startswith('HKWorkoutActivityType'):
        print('UNKNOWN WORKOUT: %s' % t)
        return
    t = t[len('HKWorkoutActivityType'):]
    time      = datestr2unix(c.attrib['startDate'])
    endtime   = datestr2unix(c.attrib['endDate'])
    delta     = endtime[0] - time[0]
    distance0 = float(c.attrib.get('totalDistance',0))
    distance  = int(distance0 * distanceScaling[c.attrib.get('totalDistanceUnit','unknown')])
    #db.insert_by_dict('workout', {
    #    'time': time[0],
    #    'tz': time[1],
    #    'duration': delta,
    #    'type': t,
    #    'distance': distance,  # in meters
    #    'source': c.attrib['sourceName']})
    #print('"{time[0]}","{}","Lon","Alt","HorAccuracy","VerAccuracy"', file=f_geo)
    for child in c:
        if child.tag == 'MetadataEntry':
            key = child.attrib['key']
            value = child.attrib['value']
            if key == 'HKWeatherTemperature':
                v = value.split(' ')
                tempr0 = float(v[0])
                if v[1] == 'degF':
                    tempr = int((tempr0 - 32) * 5/9)
                elif v[1] == 'degC':
                    tempr = int(tempr0)
                else:
                    print('Unknown temperature unit %s' % v[1])
                    #db.insert_metric(time[0], time[1], db.METRIC_TEMPERATURE, tempr)
            elif key == 'HKWeatherHumidity':
                humidity = value.split(' ')[0]
                print(f'"{time[1]}","{humidity}"')
                #db.insert_metric(time[0], time[1], db.METRIC_HUMIDITY, humidity)
        elif child.tag == 'WorkoutEvent':
            date = dateutil.parser.parse(child.attrib['date'])
            et = child.attrib['type']
            if et == 'HKWorkoutEventTypePause': pass
                #db.insert_metric(time[0], time[1], db.METRIC_WORKOUT_PAUSE_EVENT, 0)
            elif et == 'HKWorkoutEventTypeResume': pass
                #db.insert_metric(time[0], time[1], db.METRIC_WORKOUT_RESUME_EVENT, 0)
        elif child.tag == 'WorkoutRoute':
            processWorkoutRoute(child)

birthdate = 0
isFemale = 0

filename = 'export.zip'
with zipfile.ZipFile(filename) as zf:
    with zf.open('apple_health_export/export.xml') as xmlfile:
        print('Reading ', filename)
        xml_data = xmlfile.read()
print('Parsing XML')
root = ET.XML(xml_data)
print('Processing')
for c in root:
    if c.tag == 'ExportDate':
        date = dateutil.parser.parse(c.attrib['value'])
        print('Export date: {}'.format(date))
    elif c.tag == 'Me':
        birthdateStr = c.attrib.get('HKCharacteristicTypeIdentifierDateOfBirth','')
        if birthdate:
            birthdate = datestr2unix(birthdateStr)[0]
        gender = c.attrib.get('HKCharacteristicTypeIdentifierBiologicalSex')
        if gender == 'HKBiologicalSexMale':
            print('Gender: Male')
        elif gender == 'HKBiologicalSexFemale':
            print('Gender: Female')
            isFemale = 1
    elif c.tag == 'Record':
        processRecord(c)
    elif c.tag == 'Workout':
        processWorkout(c)
