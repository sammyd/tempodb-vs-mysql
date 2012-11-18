import MySQLdb as mdb
import sys
import datetime
import random
import math

def get_connection():
  return mdb.connect('localhost', 'root', 'password', 'timeseries')

def get_datapoint_at_time(conn, time, verbose=False):
  t = datetime.datetime.utcnow()
  cur = conn.cursor()
  cur.execute("SELECT SQL_NO_CACHE * FROM testSeries WHERE timestamp = %s;", (time,))
  row = cur.fetchone()
  cur.close()
  elapsed = datetime.datetime.utcnow() - t

  if verbose:
    print "value1: %f" % row[1]
    print "value2: %d" % row[2]
    print "Elapsed time: %fs" % elapsed.total_seconds()
  return elapsed.total_seconds()


def get_per_week_rollup(conn, year, rollup_function="AVG", verbose=False):
  start = datetime.datetime(year,1,1)
  end = datetime.datetime(year,2,1)

  t = datetime.datetime.utcnow()
  '''
  Although we might be able to use GROUP BY and some MySQL datetime
  functions to get MySQL to return weekly rollups, this is not trivial.
  Therefore we use successive queries to generate the information
  required
  '''
  current_dt = start
  while current_dt < end:
    cur = conn.cursor()
    current_end = current_dt + datetime.timedelta(days=7)
    query_string  = "SELECT SQL_NO_CACHE %s(value1), %s(value2) FROM testSeries WHERE timestamp > %%s AND timestamp < %%s" % (rollup_function, rollup_function)
    cur.execute(query_string, (current_dt, current_end))
    row = cur.fetchone()
    if verbose:
      print query_string, row
    cur.close()
    current_dt = current_end
  elapsed = datetime.datetime.utcnow() - t
  if verbose:
    print "Elapsed time: %fs" % elapsed.total_seconds()
  return elapsed.total_seconds()

def get_count(conn, start, end, verbose=False):
  t = datetime.datetime.utcnow()
  cur = conn.cursor()
  cur.execute("SELECT COUNT(*) FROM testSeries WHERE timestamp > %s AND timestamp < %s", (start, end))
  row = cur.fetchone()
  elapsed = dattime.datetime.utcnow() - t
  if verbose:
    print row
    print "Elapsed time: %fs" % elapsed.total_seconds()
  return elapsed.total_seconds()


def main(experiments):
  conn = get_connection()

  # Specific datapoints
  if(experiments["specific"]):
    print "Specific datapoints"
    current_dt = datetime.datetime(2000,01,01,12,00)
    elapsed_time = 0
    number_queries = 0
    while(current_dt < datetime.datetime(2005,01,01,12,00)):
      elapsed_time += get_datapoint_at_time(conn, current_dt, False)
      number_queries += 1
      current_dt += datetime.timedelta(days=30)
  
    print "Average elapsed time: %f (%d queries)" % (elapsed_time / number_queries, number_queries)

  # Weekly rollups
  if(experiments["rollup"]):
    print "Weekly Rollup :: Mean"
    elapsed_time = 0
    number_queries = 0
    for year in (2000,2001,2002,2003):
      elapsed_time += get_per_week_rollup(conn, year, "AVG", False)
      number_queries += 1
    print "Average elapsed time: %fs" % (elapsed_time / number_queries,)

  # Count
  if(experiments["count"]):
    print "Datapoint counts"
    elapsed_time = 0
    number_queries = 0
    for year in (2000,2001,2002,2003):
      start = datetime.datetime(year,2,01,12,00)
      end   = datetime.datetime(year,11,01,12,00)
      number_queries += 1
      elapsed_time += get_count(conn, start, end, True)
    print "Average elapsed time: %fs" % (elapsed_time / number_queries,)


if __name__ == '__main__':
  experiments = { "specific" : False, "rollup" : False, "count" : True }
  main(experiments)
