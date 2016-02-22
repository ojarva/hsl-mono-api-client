from local_settings import STOPS, FETCHER_INTERVAL, LINE_MAPS, LINE_DETAILS
from departures import DepartureData
import datetime
import json
import redis
import time


class Fetcher(object):
    def __init__(self):
        self.dd = DepartureData()
        self.redis = redis.StrictRedis()

    def map_lines(self, line):
        if line in LINE_MAPS:
            return LINE_MAPS[line]
        return line

    def get_line_details(self, line):
        if line in LINE_DETAILS:
            data = LINE_DETAILS[line]
        else:
            data = {"minimum_time": 0, "type": "bus", "icon": "bus"}
        data["departures"] = []
        data["visible"] = True
        data["line"] = line
        return data

    def fetch(self):
        all_departures = []
        lines = {}
        for stop_id, settings in STOPS.items():
            departures = self.dd.get_schedules(stop_id, settings)

            for departure in departures:
                line = departure.get("line")
                if not line:
                    continue
                line = self.map_lines(line)
                if line not in lines:
                    lines[line] = self.get_line_details(line)
                if departure["rtime"] is not None:
                    lines[line]["departures"].append({"timestamp": departure["rtime"], "realtime": True})
                else:
                    lines[line]["departures"].append({"timestamp": departure["time"], "realtime": False})

        for k, v in lines.items():
            sorted(v["departures"], key=lambda k: k["timestamp"])
            all_departures.append(v)
        return all_departures

    def run(self):
        all_departures = self.fetch()
        dumped = json.dumps(all_departures)
        self.redis.publish("home:broadcast:generic", json.dumps({"key": "public-transportation", "content": all_departures}))
        self.redis.setex("realtime-bus", 3600, dumped)
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
        sleep_time = max(FETCHER_INTERVAL / 2, FETCHER_INTERVAL - run_time)
        print "%s: sleeping %ss" % (datetime.datetime.now(), sleep_time)
        time.sleep(sleep_time)


if __name__ == '__main__':
    main()
