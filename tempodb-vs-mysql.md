# TempoDB as an alternative to MySQL


[TempoDB](http://www.tempo-db.com/) is an online service specialising in storing time-series data. In this article I'm going to compare using tempoDB to MySQL - a very popular relational database.

## Experiment protocol
Time series data is something that initially we will collect in relatively small amounts, but will collect it regularly for a long period of time. Therefore we want to establish how each of the systems performs not as we start using them, but how they will perform many years down the line. In order to do this I'm going to simulate 5 intensive years of time series data. We can use this to benchmark several stages of the process - including setup, data input and retrieval.

## Setup

A time series dataset is conceptually pretty simple - it consists of a set of measurements of some kind, each associated with a particular point in time. For this experiment we'll create 2 datasets - each with one datapoint per second over a period of 5 years.

### MySQL

We create a simple MySQL database, with one table in it called `testSeries`. The following python code snippet demonstrates this:

```
import MySQLdb as mdb

print "Creating the database"
con = mdb.connect('localhost', 'root', 'pass')
with con:
    cur = con.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS timeseries")
    cur.close()

print "Creating the table"
con = mdb.connect('localhost', 'root', 'pass', 'timeseries')
with con:
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS testSeries (
                       timestamp TIMESTAMP,
                       value1 DOUBLE,
                       value2 INT
                   )""")
    cur.close()
```

Note that all code used here is available on [GitHub](https://github.com/sammyd/tempodb-vs-mysql/).



### TempoDB

Preparing for data entry to TempoDB is really simple - we just have to ensure that the series we want to use have been created:

```
import tempodb

client = tempodb.Client(API_KEY, API_SECRET)

# Create the series
client.create_series('value1')
client.create_series('value2')
```

This creates 2 series - one we'll call `value1`, the other `value2` - the equivalent to the MySQL code seen above.


## Data input

We're going to populate each datastore with random values - one integer and one float, with a record every second between 12pm on January 1st, 2000 and the same time 5 years later. This will leave us with over 150 million entries, each with 2 datapoints - an integer and a float.

### MySQL

We insert a day's worth of values into the database at a time, the following code demonstrates this:

```
print "Starting %s" % datetime.datetime.utcnow()
ts = datetime.datetime(2000,1,1,12,0,0)
while(ts < datetime.datetime(2005,1,1,12,0,0)):
    con = mdb.connect('localhost', 'root', 'pass', 'timeseries')
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
```

#### MySQL Issues

In order to run this experiment I fired up a large EC2 instance and got MySQL installed. I had some problems as initially I was attempting to get 10 years of datapoints stored. This caused MySQL to fill up the instance storage space, essentially crashing the machine. With some effort, I managed to delete the data files which back the MySQL instance and restarted the process.

Other than this, the process of batch importing the data points was fairly painless.


### TempoDB

To insert the data points into TempoDB, we base the script on a python [batch import script](http://tempo-db.com/docs/batch-import/python-script/) provided by TempoDB. Since all interaction with TempoDB is performed over HTTP, we attempt to increase the speed by creating a pool of threads, each of which performs HTTP requests.

```
from Queue import Queue
from threading import Thread

class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
                sys.stdout.write('.')
                sys.stdout.flush()
            except Exception, e: print e
            self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads): Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()
```

This can then be used to parallelise the data import process:


```
    print "Starting %s" % datetime.datetime.utcnow()
    client = tempodb.Client(API_KEY, API_SECRET)

    value1_data = []
    value2_data = []
    ts = datetime.datetime(2000,1,1,12,0,0)

    # Get a threadpool together
    pool = ThreadPool(3)
    nextStop = ts + datetime.timedelta(seconds=3600)

    while(ts < datetime.datetime(2005,1,1,12,0,0)):
        if(ts >= nextStop):
            # We have enough points to submit
            pool.add_task(client.write_key, "value1", value1_data)
            pool.add_task(client.write_key, "value2", value2_data)
            value1_data = []
            value2_data = []
            nextStop = ts + datetime.timedelta(seconds=3600)

        # Add some new datapoints
        value1_data.append(tempodb.DataPoint(ts, float(random.random())))
        value2_data.append(tempodb.DataPoint(ts, long(math.floor(random.random() * 1000000))))

        # Move to the next second
        ts = ts + datetime.timedelta(seconds=1)

    # Just need to make sure that we have finished
    if(len(value1_data) > 0):
        # Some left over
        pool.add_task(client.write_key, "value1", value1_data)
        pool.add_task(client.write_key, "value2", value2_data)

    # Let's not stop before we're done
    pool.wait_completion()

    print "done %s" % datetime.datetime.utcnow()
```

#### TempoDB Issues

This code works in a similar manner to that of the MySQL import code - we collect a set of datapoints together before trying to insert them. Although initially I attempted to insert a day's worth of points with each call, it seems that 86400 datapoints is too many for TempoDB - and therefore I reduced it to insert just an hour at once.

This process is obviously likely to be slower than the equivalent over MySQL - since the MySQL import process was entirely locally. The tempoDB import script suffered a little from crashing without being complete, but I blame the lack of exception handling in the script as opposed to the underlying technology. 


## Data retrieval

This is fundamentally the most important part of the process. A time-series database is not likely to be limited by the import process, since once an initial batch import has been completed, the standard use-case is to import small amounts of data continuously.

There are several questions we want to ask of our data, which are representative of how we use time-series:

- What was the value of a specified series at a given time?
- What were the per-week means, maxima and standard deviations over a given year?
- How many data points are available within a given time period?

There are several things to consider when answering these questions:

- How difficult is it to query the data source?
- How intensive is the resultant request?

The former of these is pretty subjective, and comes down to how difficult the code was. The latter is a little more tangible, and we can derive some local benchmarks for MySQL, and a comparable time for TempoDB.

### Specific datapoint value

#### TempoDB

Retrieving specific data point values with TempoDB is fairly easy, although since it is a time-series specific datastore, we deal with time intervals instead. The following code will return the datapoint requested (since we know our temporal resolution).

```
def get_datapoint_at_time(client, time, verbose=False):
  t = datetime.datetime.utcnow()
  d = client.read(time, time + datetime.timedelta(seconds=1), keys = ['value1', 'value2'])
  elapsed = datetime.datetime.utcnow() - t

  if verbose:
    print "value1: %f" % d[0].data[0].value
    print "value2: %d" % d[1].data[0].value
    print "Elapsed time: %fs" % elapsed.total_seconds()
  return elapsed.total_seconds()
```

Repeating this across a range of 61 different time instants yielded an average data retrieval time of `0.6858s`.

#### MySQL

Finding a specific datapoint in MySQL is bread-and-butter SQL syntax:

```
mysql> SELECT * FROM testSeries WHERE timestamp = "2000-10-01 12:00:00";
+---------------------+-------------------+--------+
| timestamp           | value1            | value2 |
+---------------------+-------------------+--------+
| 2000-10-01 12:00:00 | 0.989892234959475 | 660567 |
+---------------------+-------------------+--------+
1 row in set (6 min 0.78 sec)
```

As you can see this takes a very long time - 6 minutes to find one record - compared to `0.6s` with TempoDB. However, this might not be a very fair test. This MySQL operation has to perform an complete table scan - in our case over 150 million rows.

In reality, if you were to use MySQL for this use case then you would add an index to the table based on the timestamp. This will speed up the searching, at the cost of increased write times and disk usage.

```
mysql> CREATE INDEX timestamp_index ON testSeries(timestamp);
Query OK, 0 rows affected (27 min 52.82 sec)
Records: 0  Duplicates: 0  Warnings: 0
```

This process increased the MySQL data file from 6.7GB to 9.1GB - a 35% overhead on disk usage. However, it does speed the datapoint retrieval up significantly:

```
mysql> SELECT * FROM testSeries WHERE timestamp = "2000-10-01 12:00:00";
+---------------------+-------------------+--------+
| timestamp           | value1            | value2 |
+---------------------+-------------------+--------+
| 2000-10-01 12:00:00 | 0.989892234959475 | 660567 |
+---------------------+-------------------+--------+
1 row in set (0.06 sec)
```

You can see that MySQL is using the newly created index with an `EXPLAIN` query:

```
mysql> EXPLAIN SELECT * FROM testSeries WHERE timestamp = "2000-10-01 12:00:00";
+----+-------------+------------+------+-----------------+-----------------+---------+-------+------+-------+
| id | select_type | table      | type | possible_keys   | key             | key_len | ref   | rows | Extra |
+----+-------------+------------+------+-----------------+-----------------+---------+-------+------+-------+
|  1 | SIMPLE      | testSeries | ref  | timestamp_index | timestamp_index | 4       | const |    1 |       |
+----+-------------+------------+------+-----------------+-----------------+---------+-------+------+-------+
1 row in set (0.03 sec)
```

Now we've added an index we can repeat the same experiment we used for single datapoints with TempoDB. The following code is the MySQL equivalent of that used with TempoDB:

```
def get_datapoint_at_time(conn, time, verbose=False):
  t = datetime.datetime.utcnow()
  cur = conn.cursor()
  cur.execute("SELECT * FROM testSeries WHERE timestamp = %s;", (time,))
  row = cur.fetchone()
  cur.close()
  elapsed = datetime.datetime.utcnow() - t

  if verbose:
    print "value1: %f" % row[1]
    print "value2: %d" % row[2]
    print "Elapsed time: %fs" % elapsed.total_seconds()
  return elapsed.total_seconds()
```

We again run this over 61 distinct time instants, which yields an average datapoint retrieval time of `0.0281s`.

### Rollups

Rollups are the ability to summarise the datapoints over a given temporal range - e.g. the average/max value of a series in a given month. This is particularly useful in timeseries, since it is often these trends which are of high importance when investigating the data.

#### TempoDB
TempoDB has built-in support for common rollup functions - and as such access to them is pretty simple. For example, the following method will take a client, and a given rollup function and return the rolled-up across all the weeks in a given year:

```
def get_per_week_rollup(client, year, rollup_function, verbose=False):
  start = datetime.datetime(year,1,1)
  end = datetime.datetime(year+1,1,1)

  t = datetime.datetime.utcnow()
  d = client.read(start,end, keys=['value1'], interval="7day", function=rollup_function)
  elapsed = datetime.datetime.utcnow() - t

  if verbose:
    print "Elapsed time: %fs" % elapsed.total_seconds()
  return elapsed.total_seconds()
```

This can be used with rollup functions such as `mean`, `sum`, `max`, `min`, and `stddev`.

#### MySQL
__TODO__

### Datapoint count

#### TempoDB
TempoDB has `count` as one of their standard rollup functions, and therefore we can use the same code a we did before to establish the count.

#### MySQL
__TODO__