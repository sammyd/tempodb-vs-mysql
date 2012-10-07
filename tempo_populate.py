import tempodb
import random
import datetime
import math
from Queue import Queue
from threading import Thread
import sys


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


def main():
    print "Starting %s" % datetime.datetime.utcnow()
    client = tempodb.Client('8ece39345db74685ac1bff751f636254', '33efe4bba03b4a97a9dffdc6bac2008c')

    # Create the series
    client.create_series('testSeries')
    client.create_series('value1')
    client.create_series('value2')

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

if __name__ == '__main__':
    main()



