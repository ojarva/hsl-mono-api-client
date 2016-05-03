# pylint:disable=line-too-long

"""HSL realtime fetcher

Usage:
    fetch_realtime.py run --config=<config_file> [--debug] [--verbose] [--redis_port=<port>] [--redis_host=<hostname>] [--redis_db=<db>] [--redis_password=<password>]
    fetch_realtime.py single-run --config=<config_file> [--debug] [--verbose] [--redis_port=<port>] [--redis_host=<hostname>] [--redis_db=<db>] [--redis_password=<password>]

Options:
    --config=<config_file>       Path to configuration file
    --debug                      Enable debug logging
    --verbose                    Print out fetched data (but no debug logging, can be combined with --debug)
    --redis_port=<port>          Port for redis server [default: 6379]
    --redis_host=<hostname>      Hostname for redis server [default: localhost]
    --redis_db=<db number>       Redis database [default: 0]
    --redis_password=<password>  Password for redis
"""

import imp
import json
import logging
import pprint
import socket
import sys
import time

import docopt
import redis
from departures import DepartureData


class Fetcher(object):

    def __init__(self, config, **kwargs):
        self.verbose = kwargs.get("verbose", False)
        self.config = config
        self.departure_data = DepartureData()
        redis_args = {
            "host": kwargs.get("redis_host", "localhost"),
            "port": int(kwargs.get("redis_port", 6379)),
            "db": int(kwargs.get("redis_db", 0)),
            "password": kwargs.get("redis_password", None),
        }
        self.redis = redis.StrictRedis(**redis_args)
        self.logger = logging.getLogger("fetch-hsl-realtime")
        if kwargs.get("debug"):
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        format_string = "%(asctime)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(format_string)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.check_config(config)

    def check_config(self, config):
        for arg in ("STOPS", "LINE_MAPS", "LINE_DETAILS"):
            try:
                value = getattr(config, arg)
            except AttributeError:
                self.logger.error("Invalid configuration file - %s is not set.", arg)
                sys.exit(2)
            if not isinstance(value, dict):
                self.logger.error("Invalid configuration file - %s must be a dict.", arg)
                sys.exit(2)

        for arg in ("FETCHER_INTERVAL", "REDIS_PUBSUB_KEY", "REDIS_STATIC_KEY"):
            try:
                value = getattr(config, arg)
            except AttributeError:
                self.logger.debug("Missing optional key %s - disables some functionality.", arg)

    def _map_lines(self, line):
        if line in self.config.LINE_MAPS:
            return self.config.LINE_MAPS[line]
        return line

    def _get_line_details(self, line):
        if line in self.config.LINE_DETAILS:
            data = self.config.LINE_DETAILS[line]
        else:
            data = {"minimum_time": 0, "type": "bus", "icon": "bus"}
        data["departures"] = []
        data["visible"] = True
        data["line"] = line
        return data

    def fetch(self):
        """ Fetch all configured departures but does not update redis. """
        all_departures = []
        lines = {}
        for stop_id, settings in self.config.STOPS.items():
            self.logger.debug("Fetching departures for stop %s: %s", stop_id, settings)
            try:
                departures = self.departure_data.get_schedules(stop_id, settings)
            except socket.timeout as err:
                self.logger.info("Fetching departures for %s failed with timeout", stop_id)
                raise err

            self.logger.debug("Received %s for stop %s", departures, stop_id)
            for departure in departures:
                line = departure.get("line")
                if not line:
                    continue
                line = self._map_lines(line)
                if line not in lines:
                    lines[line] = self._get_line_details(line)
                if departure["rtime"] is not None:
                    data = {"timestamp": departure["rtime"], "realtime": True}
                else:
                    data = {"timestamp": departure["time"], "realtime": False}
                data["departure_id"] = departure["id"]
                lines[line]["departures"].append(data)

        for key, value in lines.items():  # pylint:disable=unused-variable
            value["departures"] = sorted(value["departures"], key=lambda key: key["timestamp"])
            all_departures.append(value)
        all_departures = sorted(all_departures, key=lambda key: key["line"])
        return all_departures

    def run(self):
        """ Fetch all configured departures once and publish to redis. """
        try:
            all_departures = self.fetch()
        except socket.timeout:
            self.logger.info("Not all departure fetches succeeded - skip publishing updates.")
            return None
        dumped = json.dumps(all_departures)
        try:
            self.redis.publish(self.config.REDIS_PUBSUB_KEY, json.dumps({"key": "public-transportation", "content": all_departures}))
        except AttributeError:
            self.logger.debug("Not publishing to pubsub - REDIS_PUBSUB_CHANNEL is not set.")
        try:
            self.redis.setex(self.config.REDIS_STATIC_KEY, self.config.REDIS_STATIC_TTL, dumped)
        except AttributeError:
            self.logger.debug("Not setting data to static redis key - REDIS_KEY is not set.")
        if self.verbose:
            pprint.pprint(all_departures)
        return all_departures

    def loop(self):
        """ Fetch all configured departures and publish to redis. Loop forever, and sleep FETCHER_INTERVAL seconds between each loop. """
        while True:
            self.logger.info("Starting")
            run_started = time.time()
            self.run()
            run_finished = time.time()
            run_time = run_finished - run_started
            self.logger.info("Finished in %ss", run_time)
            try:
                if self.config.FETCHER_INTERVAL is None:
                    self.logger.info("FETCHER_INTERVAL is not set - not running the loop")
                    return
            except AttributeError:
                self.logger.info("FETCHER_INTERVAL is not set - not running the loop")
                return
            sleep_time = max(self.config.FETCHER_INTERVAL / 2, self.config.FETCHER_INTERVAL - run_time)
            self.logger.info("Sleeping for %ss", sleep_time)
            time.sleep(sleep_time)


def main():  # pylint:disable=missing-docstring
    arguments = docopt.docopt(__doc__, version='HSL realtime fetcher 1.0')
    config = imp.load_source("config", arguments["--config"])
    fetcher = Fetcher(config, debug=arguments.get("--debug"), verbose=arguments.get("--verbose"), redis_port=arguments.get("--redis_port"), redis_host=arguments.get("--redis_host"), redis_db=arguments.get("--redis_db"), redis_password=arguments.get("--redis_password"))
    if arguments["run"]:
        fetcher.loop()
    elif arguments["single-run"]:
        fetcher.run()

if __name__ == '__main__':
    main()
