# coding=utf-8
# pylint:disable=line-too-long

import datetime
import pprint

import cachetools
import suds
import pytz


class DepartureData(object):

    cache = cachetools.TTLCache(20, 30)

    def __init__(self):
        self.client = suds.client.Client("http://omatlahdot.hkl.fi/interfaces/kamo?wsdl")
        self.timezone = pytz.timezone("Europe/Helsinki")

    def _convert_list(self, item_list, original_timestamp):
        return [self._convert_item(item, original_timestamp) for item in item_list]

    def _convert_time(self, value, original_timestamp):
        if value is None:
            return None
        parsed = datetime.datetime.strptime(value, "%H:%M:%S")
        combined = datetime.datetime.combine(datetime.datetime.today(), parsed.time())
        time_diff = combined - original_timestamp
        if time_diff < -datetime.timedelta(hours=10):
            combined += datetime.timedelta(days=1)

        return self.timezone.localize(combined).isoformat()

    def _convert_item(self, item, original_timestamp):
        data = {}
        for k, val in item:
            if k in ("time", "rtime"):
                val = self._convert_time(val, original_timestamp)
            if isinstance(val, suds.sax.text.Text):
                data[k] = val.encode("utf-8")
            else:
                data[k] = val
        return data

    @cachetools.cached(cache)
    def scheduled_departures(self, stop_id, timestamp=None, departures_count=20):
        """ Return scheduled departures (as opposed to departures based on realtime information).

        If timestamp is set, returns departures after given timestamp, otherwise now.
        If departures_count is set, limits number of returned departures. """
        if timestamp is None:
            timestamp = datetime.datetime.now()
        timestamp_formatted = timestamp.isoformat()
        departures = self.client.service.getNextDeparturesExt(String_1=stop_id, Date_2=timestamp_formatted, int_3=departures_count)
        return self._convert_list(departures, timestamp)

    @cachetools.cached(cache)
    def realtime_departures(self, stop_id, timestamp=None, departures_count=20):
        """ Return realtime departures for given stop, without filtering.

        If timestamp (datetime.datetime) is set, returns departures after given timestamp, otherwise now.
        If departures_count is set, limits number of returned departures. """
        if timestamp is None:
            timestamp = datetime.datetime.now()
        timestamp_formatted = timestamp.isoformat()
        departures = self.client.service.getNextDeparturesExtRT(String_1=stop_id, Date_2=timestamp_formatted, int_3=departures_count)
        return self._convert_list(departures, timestamp)

    @cachetools.cached(cache)
    def rest_of_the_route(self, passing_id):
        """ Return rest of the route basd on passing_id. passing_id can be found from .realtime_departures or .scheduled_departures responses. """
        departures = self.client.service.getPassingTimes(String_1=passing_id)
        return self._convert_list(departures, datetime.datetime.now())

    def get_schedules(self, stop_id, stop_settings, timestamp=None):
        """ Returns filtered departures for given stop.

        stop_settings is a dict with "show_lines" list (or tuple), that is used for filtering.
        If stop_settings["show_lines"] is not set or None, no filtering will be done.

        If timestamp (datetime.datetime) is set, fetches departures after given timestamp, otherwise now. """
        departures = self.realtime_departures(stop_id, timestamp)
        show_lines = stop_settings.get("show_lines")
        if show_lines:
            departures = [departure for departure in departures if departure["line"] in show_lines]
        return departures


def _main():  # pylint:disable=missing-docstring
    departure_data = DepartureData()
    deplist = departure_data.get_schedules("1113131", {"name": "Sörnäinen", "show_lines": ["65A", "66A"]})
    pprint.pprint(deplist)

if __name__ == '__main__':
    _main()
