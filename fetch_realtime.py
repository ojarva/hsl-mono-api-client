from local_settings import STOPS, FETCHER_INTERVAL, LINE_MAPS, LINE_DETAILS
from departures import DepartureData
import datetime
import json
import redis
import time
import socket


class Fetcher(object):
    def __init__(self):
        self.dd = DepartureData()
        self.redis = redis.StrictRedis()

    @classmethod
    def log(cls, message, **kwargs):
        formatted_message = message.format(**kwargs)
        print "{timestamp}: {message}".format(message=formatted_message, timestamp=datetime.datetime.now())

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
            try:
                departures = self.dd.get_schedules(stop_id, settings)
            except socket.timeout as err:
                self.log("fetching departures for {stop_id} failed with timeout", stop_id=stop_id)
                raise err

            for departure in departures:
                line = departure.get("line")
                if not line:
                    continue
                line = self.map_lines(line)
                if line not in lines:
                    lines[line] = self.get_line_details(line)
                if departure["rtime"] is not None:
                    data = {"timestamp": departure["rtime"], "realtime": True}
                else:
                    data = {"timestamp": departure["time"], "realtime": False}
                data["departure_id"] = departure["id"]
                lines[line]["departures"].append(data)

        for k, v in lines.items():
            v["departures"] = sorted(v["departures"], key=lambda k: k["timestamp"])
            all_departures.append(v)
        all_departures = sorted(all_departures, key=lambda k: k["line"])
        return all_departures

    def run(self):
        try:
            all_departures = self.fetch()
        except socket.timeout:
            self.log("not all departure fetches succeeded - skip publishing updates.")
            return None
        dumped = json.dumps(all_departures)
        self.redis.publish("home:broadcast:generic", json.dumps({"key": "public-transportation", "content": all_departures}))
        self.redis.setex("realtime-bus", 3600, dumped)
        return all_departures

    def loop(self):
        while True:
            self.log("starting")
            run_started = time.time()
            self.run()
            run_finished = time.time()
            run_time = run_finished - run_started
            self.log("finished in {run_time}s", run_time=run_time)
            if FETCHER_INTERVAL is None:
                return
            sleep_time = max(FETCHER_INTERVAL / 2, FETCHER_INTERVAL - run_time)
            self.log("sleeping {sleep_time}s", sleep_time=sleep_time)
            time.sleep(sleep_time)


def main():
    fetcher = Fetcher()
    fetcher.loop()

if __name__ == '__main__':
    main()
