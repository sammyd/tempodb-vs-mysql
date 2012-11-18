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


if __name__ == '__main__':
  main()
