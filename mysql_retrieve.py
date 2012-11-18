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
  cur.execute("SELECT * FROM testSeries WHERE timestamp = %s;", (time,))
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
    cur.execute("SELECT %s(value1), %s(value2) FROM testSeries WHERE timestamp > %s AND timestamp < %s", (rollup_function, rollup_function, current_dt, current_end))
    row = cur.fetchone()
    cur.close()
    current_dt = current_end
  elapsed = datetime.datetime.utcnow() - t
  if verbose:
    print "Elapsed time: %fs" % elapsed.total_seconds()
  return elapsed.total_seconds()


def main():
  conn = get_connection()

  # Specific datapoints
  print "Specific datapoints"
  current_dt = datetime.datetime(2000,01,01,12,00)
  elapsed_time = 0
  number_queries = 0
  while(current_dt < datetime.datetime(2005,01,01,12,00)):
    elapsed_time += get_datapoint_at_time(conn, current_dt, True)
    number_queries += 1
    current_dt += datetime.timedelta(days=30)

  print "Average elapsed time: %f (%d queries)" % (elapsed_time / number_queries, number_queries)

  # Weekly rollups
  print "Weekly Rollup :: Mean"
  elapsed_time = 0
  number_queries = 0
  for year in (2000,2001,2002,2003):
    elapsed_time += get_per_week_rollup(conn, year, "AVG", True)
    number_queries += 1
  print "Average elapsed time: %fs" % elapsed_time / number_queries


if __name__ == '__main__':
  main()
