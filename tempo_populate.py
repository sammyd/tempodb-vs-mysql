import tempodb
import random
import datetime
import math
import utils.threading as threading

# Set the start and end times here. This is lazy.
start_time = datetime.datetime(2010, 1, 1, 12, 0, 1)
end_time   = datetime.datetime(2015, 1, 1, 12, 0, 0)


def main(t_start, t_end, no_threads=3):
    print "Starting %s" % datetime.datetime.utcnow()

    # Create the client
    client = tempodb.Client('8ece39345db74685ac1bff751f636254', '33efe4bba03b4a97a9dffdc6bac2008c')

    value1_data = []
    value2_data = []
    ts = t_start

    # Get a threadpool together
    pool = threading.ThreadPool(no_threads)
    nextStop = ts + datetime.timedelta(seconds=3600)

    while(ts < t_end):
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
    main(start_time, end_time, 3)
