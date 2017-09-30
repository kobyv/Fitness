Activity Database
=================

A set of Python3 scripts to import and export activity / work / health data into a common format — a SQLite database.

All scripts assume that the database resides in the current directory and is named `activity.db`.

Available conversions:
*  Import Apple health database and append (only new items) to `activity.db`.
*  Import GPX and append to `activity.db`.
*  View workouts and export as GPX.

In case that append is not desired, delete `activity.db` and a new one will be created instead.

The database holds the "important" information found in the Apple health database, including heart rate, step count, flights climbed, even if not during a workout.
In addition, workouts, with route (and heart rate data), pause/resume events and weather are stored.

## Why?

*   Consolidate all activity sources.
    If only I could import workouts with routes to the iPhone health database...

*   Upload Apple watch workouts recorded with the internal workout app, including route, to fitness cloud providers (Strava, etc.).

*   A very simple format to be used as in input to data analysis tools.

## Workouts Script

List all activities:
```
./workout.py --list
```
The result is a CSV containing all workouts.
It can be directed to a file and opened by, e.g., Excel:
```
./workout.py --list > workouts.csv
open workouts.csv   # in MacOS
```

Activities are referred by their starting date, as appears in the CSV.
So, if the CSV looks like:
```
Time,Type,Source,Duration [mins],Distance [m]
2017-09-02T07:43:57+0300,Running,Strava,35,5769
2017-09-19T08:28:30+0300,Running,Runkeeper,40,6649
2017-09-19T21:24:07+0300,Cycling,Koby’s Apple Watch,16,3611
2017-09-21T08:28:48+0300,Running,iSmoothRun,34,5867
```
Then the cycling recorded on the Apple watch, can be exported to GPX as follows:
```
./workout.py --gpx "2017-09-19T21:24:07+0300"
```

## iPhone Apple Health Converter

iOS11 allows full export of Apple Heath database, including routes in workouts, although location coordinates are trancated to around 10 m resolution.

From the Health app, press the upper right "face" icon, and choose "Export Health Data".
Send the resulting `export.zip` to a computer (AirDrop is the fastest if using a Mac).

In the current directory `export.zip`, and previous `activity.db` (if present) should reside.

Execute:
```
./import_health.py
```

The script is super-slow, so be patient.  
**TODO**: make it faster!

## Database

The database is a simple SQLite file.

Standard backup and restore can be done using the `sqlite3` client:

```
# Dump
sqlite3 activity.db .dump > activity_backup.sql

# Restore (activity.db does not have to exist)
sqlite3 activity.db < activity_backup.sql
```

The backup is highly compressible.

See `db.py`.

LICENSE: MIT
