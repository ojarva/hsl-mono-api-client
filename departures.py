# coding=utf-8

import cachetools
import datetime
import pprint
import suds


class DepartureData(object):

    cache = cachetools.TTLCache(20, 30)

    def __init__(self):
        self.client = suds.client.Client("http://omatlahdot.hkl.fi/interfaces/kamo?wsdl")

    @classmethod
    def convert_list(cls, item_list):
        return [cls.convert_item(item) for item in item_list]

    @classmethod
    def convert_item(cls, item):
        data = {}
        for k, val in item:
            if isinstance(val, suds.sax.text.Text):
                data[k] = val.encode("utf-8")
            else:
                data[k] = val
        return data

    @cachetools.cached(cache)
    def scheduled_departures(self, stop_id, timestamp=None, departures_count=20):
        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        departures = self.client.service.getNextDeparturesExt(String_1=stop_id, Date_2=timestamp, int_3=departures_count)
        return self.convert_list(departures)

    @cachetools.cached(cache)
    def realtime_departures(self, stop_id, timestamp=None, departures_count=20):
        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        departures = self.client.service.getNextDeparturesExtRT(String_1=stop_id, Date_2=timestamp, int_3=departures_count)
        return self.convert_list(departures)

    @cachetools.cached(cache)
    def rest_of_the_route(self, passing_id):
        departures = self.client.service.getPassingTimes(String_1=passing_id)
        return self.convert_list(departures)

    def get_schedules(self, stop_id, stop_settings):
        departures = self.realtime_departures(stop_id)
        show_lines = stop_settings.get("show_lines")
        if show_lines:
            departures = [departure for departure in departures if departure["line"] in show_lines]
        return departures


def main():
    rd = DepartureData()
#    deplist = rd.realtime_departures("1121124")
#    deplist = rd.rest_of_the_route("564342016")
    deplist = rd.get_schedules("1113131", {"name": "Sörnäinen",
                                           "show_lines": ["65A", "66A"], })
    pprint.pprint(deplist)

if __name__ == '__main__':
    main()
