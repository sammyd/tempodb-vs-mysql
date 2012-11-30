import MySQLdb as mdb
import datetime
import random
import math
import utils.threadpool as tp

# Set the start and end times here. This is lazy.
start_date = datetime.datetime(2010, 1, 1, 12, 0, 1)
end_date   = datetime.datetime(2015, 1, 1, 12, 0, 0)


def prepare_database():
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


def insert_values(data):
    con = mdb.connect('localhost', 'root', 'password', 'timeseries')
    with con:
        cur = con.cursor()
        cur.executemany("INSERT INTO testSeries(timestamp, value1, value2) VALUES (%s, %s, %s)", data)
        cur.close()


def main(t_start, t_end, no_threads):
    # Prepare the database
    prepare_database()

    # Beginning the data point insertion
    print "Starting %s" % datetime.datetime.utcnow()

    # Let's create a threadpool
    pool = tp.ThreadPool(no_threads)

    ts = t_start
    while(ts < t_end):
        insertValues = []
        nextStop = ts + datetime.timedelta(days=1)
        while(ts < nextStop):
            v1 = random.random()
            v2 = math.floor(random.random() * 1000000)
            insertValues.append((ts, v1, v2))
            ts = ts + datetime.timedelta(seconds=1)

        # Push the new job to the pool
        pool.add_task(insert_values, insertValues)

    # Let's not stop before we're done
    pool.wait_completion()

    print "done %s" % datetime.datetime.utcnow


if __name__ == '__main__':
    main(start_date, end_date, 3)
