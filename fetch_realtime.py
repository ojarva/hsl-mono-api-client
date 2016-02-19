from local_settings import STOPS, FETCHER_INTERVAL
from departures import DepartureData
import datetime
import json
import redis
import time


class Fetcher(object):
    def __init__(self):
        self.dd = DepartureData()
        self.redis = redis.StrictRedis()

    def fetch(self):
        all_departures = []
        for stop_id, settings in STOPS.items():
            departures = self.dd.get_schedules(stop_id, settings)
            all_departures.append({
                "name": settings["name"],
                "departures": departures,
            })
        return all_departures

    def run(self):
        all_departures = self.fetch()
        self.redis.publish("realtime-bus-departures", json.dumps(all_departures))
        return all_departures


def main():
    fetcher = Fetcher()
    while True:
        print "%s: starting" % (datetime.datetime.now())
        run_started = time.time()
        fetcher.run()
        run_finished = time.time()
        run_time = run_finished - run_started
        print "%s: finished in %ss" % (datetime.datetime.now(), run_time)
        if FETCHER_INTERVAL is None:
            return
        sleep_time = FETCHER_INTERVAL - run_time
        print "%s: sleeping %ss" % (datetime.datetime.now(), sleep_time)
        time.sleep(sleep_time)


if __name__ == '__main__':
    main()
