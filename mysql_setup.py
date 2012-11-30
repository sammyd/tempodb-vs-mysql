import MySQLdb as mdb
import sys
import datetime
import random
import math

print "Creating the database"
con = mdb.connect('localhost', 'root', 'password')
with con:
    cur = con.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS timeseries")
    cur.close()

print "Creating the table"
con = mdb.connect('localhost', 'root', 'password', 'timeseries')
with con:
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS testSeries (
                       timestamp TIMESTAMP,
                       value1 DOUBLE,
                       value2 INT
                   )""")
    cur.close()


print "Starting %s" % datetime.datetime.utcnow()
ts = datetime.datetime(2005,1,1,12,0,1)
while(ts < datetime.datetime(2010,1,1,12,0,0)):
    con = mdb.connect('localhost', 'root', 'password', 'timeseries')
    with con:
        cur = con.cursor()
        insertValues = []
        nextStop = ts + datetime.timedelta(days=1)
        while(ts < nextStop):
            v1 = random.random()
            v2 = math.floor(random.random() * 1000000)
            insertValues.append((ts, v1, v2))
            ts = ts + datetime.timedelta(seconds=1)

        sys.stdout.write('.')
        sys.stdout.flush()
        cur.executemany("INSERT INTO testSeries(timestamp, value1, value2) VALUES (%s, %s, %s)", insertValues)
        cur.close()

print "done %s" % datetime.datetime.utcnow()
