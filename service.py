from departures import DepartureData
from fetch_realtime import Fetcher
from flask import Flask
from flask_restful import Resource, Api
from flask_restful_url_generator import UrlList
from flask.ext.cors import CORS
import os

app = Flask("helmi-departures")
api = Api(app)
CORS(app)

dd = DepartureData()
fetcher = Fetcher()


class RealtimeDepartures(Resource):
    """ Realtime departures for specified stop """
    def get(self, stop_id):
        departures = dd.realtime_departures(stop_id)
        return departures


class LineStops(Resource):
    """ Returns next stops for specified departure. Fetch departure_id from /stop/<stop_id> endpoint. """
    def get(self, departure_id):
        return dd.rest_of_the_route(departure_id)


class ConfiguredDepartures(Resource):
    """ Returns departures configured in local_settings """

    def get(self):
        return fetcher.fetch()


api.add_resource(LineStops, "/line/<departure_id>")
api.add_resource(RealtimeDepartures, "/stop/<stop_id>")
api.add_resource(ConfiguredDepartures, "/departures")
api.add_resource(UrlList, "/", resource_class_kwargs={"api": api})


def main():
    port = int(os.environ.get('PORT', 5019))
    app.run(host='0.0.0.0', port=port, debug=True)


if __name__ == '__main__':
    main()
