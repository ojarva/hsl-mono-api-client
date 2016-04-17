# coding=utf-8

import cachetools
import datetime
import pprint
import suds
import pytz


class DepartureData(object):

    cache = cachetools.TTLCache(20, 30)

    def __init__(self):
        self.client = suds.client.Client("http://omatlahdot.hkl.fi/interfaces/kamo?wsdl")
        self.timezone = pytz.timezone("Europe/Helsinki")

    def convert_list(self, item_list, original_timestamp):
        return [self.convert_item(item, original_timestamp) for item in item_list]

    def convert_time(self, value, original_timestamp):
        if value is None:
            return None
        parsed = datetime.datetime.strptime(value, "%H:%M:%S")
        combined = datetime.datetime.combine(datetime.datetime.today(), parsed.time())
        time_diff = combined - original_timestamp
        if time_diff < -datetime.timedelta(hours=10):
            combined += datetime.timedelta(days=1)

        return self.timezone.localize(combined).isoformat()

    def convert_item(self, item, original_timestamp):
        data = {}
        for k, val in item:
            if k in ("time", "rtime"):
                val = self.convert_time(val, original_timestamp)
            if isinstance(val, suds.sax.text.Text):
                data[k] = val.encode("utf-8")
            else:
                data[k] = val
        return data

    @cachetools.cached(cache)
    def scheduled_departures(self, stop_id, timestamp=None, departures_count=20):
        if timestamp is None:
            timestamp = datetime.datetime.now()
        timestamp_formatted = timestamp.isoformat()
        departures = self.client.service.getNextDeparturesExt(String_1=stop_id, Date_2=timestamp_formatted, int_3=departures_count)
        return self.convert_list(departures, timestamp)

    @cachetools.cached(cache)
    def realtime_departures(self, stop_id, timestamp=None, departures_count=20):
        if timestamp is None:
            timestamp = datetime.datetime.now()
        timestamp_formatted = timestamp.isoformat()
        departures = self.client.service.getNextDeparturesExtRT(String_1=stop_id, Date_2=timestamp_formatted, int_3=departures_count)
        return self.convert_list(departures, timestamp)

    @cachetools.cached(cache)
    def rest_of_the_route(self, passing_id):
        departures = self.client.service.getPassingTimes(String_1=passing_id)
        return self.convert_list(departures, datetime.datetime.now())

    def get_schedules(self, stop_id, stop_settings, timestamp=None):
        departures = self.realtime_departures(stop_id, timestamp)
        show_lines = stop_settings.get("show_lines")
        if show_lines:
            departures = [departure for departure in departures if departure["line"] in show_lines]
        return departures


def main():
    rd = DepartureData()
    deplist = rd.get_schedules("1113131", {"name": "Sörnäinen",
                                           "show_lines": ["65A", "66A"]})
    pprint.pprint(deplist)

if __name__ == '__main__':
    main()
