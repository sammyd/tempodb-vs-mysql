import tempodb
import datetime


def get_datapoint_at_time(client, time, verbose=False):
  t = datetime.datetime.utcnow()
  d = client.read(time, time + datetime.timedelta(seconds=1), keys = ['value1', 'value2'])
  elapsed = datetime.datetime.utcnow() - t

  if verbose:
    print "value1: %f" % d[0].data[0].value
    print "value2: %d" % d[1].data[0].value
    print "Elapsed time: %fs" % elapsed.total_seconds()
  return elapsed.total_seconds()


def get_per_week_rollup(client, year, rollup_function, verbose=False):
  start = datetime.datetime(year,1,1)
  end = datetime.datetime(year,2,1)

  t = datetime.datetime.utcnow()
  d = client.read(start,end, keys=['value1'], interval="7day", function=rollup_function)
  elapsed = datetime.datetime.utcnow() - t

  if verbose:
    print "Elapsed time: %fs" % elapsed.total_seconds()
  return elapsed.total_seconds()


def main():
  client = tempodb.Client('8ece39345db74685ac1bff751f636254', '33efe4bba03b4a97a9dffdc6bac2008c')

  # Specific datapoints
  if (1==0):
    print "Specific datapoints"
    current_dt = datetime.datetime(2000,01,01,12,00)
    elapsed_time = 0
    number_queries = 0
    while(current_dt < datetime.datetime(2005,01,01,12,00)):
      elapsed_time += get_datapoint_at_time(client, current_dt)
      number_queries += 1
      current_dt += datetime.timedelta(days=30)

    print "Average elapsed time: %f (%d queries)" % (elapsed_time / number_queries, number_queries)

  # Weekly rollups
  print "Weekly Rollup :: Mean"
  elapsed_time = 0
  number_queries = 0
  for year in (2000,2001,2002,2003):
    elapsed_time += get_per_week_rollup(client, year, "mean", True)
    number_queries += 1
  print "Average elapsed time: %fs" % (elapsed_time / number_queries,)


if __name__ == '__main__':
  main()


