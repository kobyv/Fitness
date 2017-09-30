#!/usr/bin/env python3

import os, zipfile, datetime, dateutil.parser, json
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict, Any
import db

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

basicRecordTypes = {
    'Height':         db.METRIC_HEIGHT,
    'BodyMass':       db.METRIC_WEIGHT,
    'HeartRate':      db.METRIC_HR,
    'FlightsClimbed': db.METRIC_FLIGHTSCLIMBED,
    'StepCount':      db.METRIC_STEPCOUNT
    }

prev_metric = 0  # just for printing

def processRecord(c):
    # type: (ET.Element) -> None
    t = c.attrib['type']
    if not t.startswith('HKQuantityTypeIdentifier'):  # can also be HKCategoryTypeIdentifier
        return
    t = t[len('HKQuantityTypeIdentifier'):]
    #all_tags[t] = 1
    valuef   = float(c.attrib['value'])
    value    = int(valuef)
    unit     = c.attrib.get('unit')
    time     = db.datestr2unix(c.attrib['startDate'])
    endtime  = db.datestr2unix(c.attrib['endDate'])
    delta    = endtime[0] - time[0]
    metric = basicRecordTypes.get(t, 0)
    global prev_metric
    if metric:
        db.insert_metric(time[0], time[1], metric, value, delta)
        if metric != prev_metric:
            print("Metric:", t)
            prev_metric = metric

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

def processWorkoutRoute(xml_elem):
    # type: (ET.Element) -> None
    for c in xml_elem:
        if c.tag != 'Location': continue
        time = db.datestr2unix(c.attrib['date'])
        lat = int(float(c.attrib['latitude']) * db.deg2db)
        lon = int(float(c.attrib['longitude']) * db.deg2db)
        alt = int(float(c.attrib['altitude']) * 100)
        db.insert_location(time[0], time[1], lat, lon, alt)

distanceScaling = {'km': 1000, 'm':1, 'unknown':0}

def processWorkout(c):
    # type: (ET.Element) -> None
    t = c.attrib['workoutActivityType']
    if not t.startswith('HKWorkoutActivityType'):
        print('UNKNOWN WORKOUT: %s' % t)
        return
    t = t[len('HKWorkoutActivityType'):]
    time      = db.datestr2unix(c.attrib['startDate'])
    endtime   = db.datestr2unix(c.attrib['endDate'])
    delta     = endtime[0] - time[0]
    distance0 = float(c.attrib.get('totalDistance',0))
    distance  = int(distance0 * distanceScaling[c.attrib.get('totalDistanceUnit','unknown')])
    db.insert_by_dict('workout', {
        'time': time[0],
        'tz': time[1],
        'duration': delta,
        'type': t,
        'distance': distance,  # in meters
        'source': c.attrib['sourceName']})
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
                    db.insert_metric(time[0], time[1], db.METRIC_TEMPERATURE, tempr)
            elif key == 'HKWeatherHumidity':
                humidity = int(float(value.split(' ')[0]))
                db.insert_metric(time[0], time[1], db.METRIC_HUMIDITY, humidity)
        elif child.tag == 'WorkoutEvent':
            date = dateutil.parser.parse(child.attrib['date'])
            et = child.attrib['type']
            if et == 'HKWorkoutEventTypePause':
                db.insert_metric(time[0], time[1], db.METRIC_WORKOUT_PAUSE_EVENT, 0)
            elif et == 'HKWorkoutEventTypeResume':
                db.insert_metric(time[0], time[1], db.METRIC_WORKOUT_RESUME_EVENT, 0)
        elif child.tag == 'WorkoutRoute':
            processWorkoutRoute(child)

db.connect()
db.start_insertions()
birthdate = 0
isFemale = 0

filename = 'export.zip'
with zipfile.ZipFile(filename) as zf:
    with zf.open('apple_health_export/export.xml') as xmlfile:
        print('Reading ', filename)
        xml_data = xmlfile.read()
print('Parsing XML')
root = ET.XML(xml_data)
for c in root:
    if c.tag == 'ExportDate':
        date = dateutil.parser.parse(c.attrib['value'])
        print('Export date: {}'.format(date))
    elif c.tag == 'Me':
        birthdateStr = c.attrib.get('HKCharacteristicTypeIdentifierDateOfBirth')
        if birthdate:
            birthdate = db.datestr2unix(birthdateStr)[0]
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

db.set_me(birthdate, isFemale)
db.commit_insertions()
db.close()
