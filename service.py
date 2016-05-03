# pylint:disable=line-too-long

"""HSL realtime departures proxy server

Usage:
    service.py run --config=<config_file> [--port=<port>] [--debug]

Options:
    --port=<port>  Port number to listen on [default: 5019]
    --debug        Print debug output, including stack traces and all the requests
"""
import os
import imp

import docopt
from flask import Flask
from flask_restful import Resource, Api
from flask_restful_url_generator import UrlList
from flask.ext.cors import CORS  # pylint:disable=no-name-in-module,import-error
from departures import DepartureData
from fetch_realtime import Fetcher

app = Flask("helmi-departures")  # pylint:disable=invalid-name
api = Api(app)  # pylint:disable=invalid-name
CORS(app)


class RealtimeDepartures(Resource):
    """ Realtime departures for specified stop """

    def get(self, stop_id):  # pylint:disable=no-self-use,missing-docstring
        departures = app.departures_data.realtime_departures(stop_id)
        return departures


class LineStops(Resource):
    """ Returns next stops for specified departure. Fetch departure_id from /stop/<stop_id> endpoint. """

    def get(self, departure_id):  # pylint:disable=no-self-use,missing-docstring
        return app.departures_data.rest_of_the_route(departure_id)


class ConfiguredDepartures(Resource):
    """ Returns departures configured in local_settings """

    def get(self):  # pylint:disable=no-self-use,missing-docstring
        return app.fetcher.fetch()


api.add_resource(LineStops, "/line/<departure_id>")
api.add_resource(RealtimeDepartures, "/stop/<stop_id>")
api.add_resource(ConfiguredDepartures, "/departures")
api.add_resource(UrlList, "/", resource_class_kwargs={"api": api})


def main():  # pylint:disable=missing-docstring
    arguments = docopt.docopt(__doc__, version='HSL realtime departures proxy')
    port = int(os.environ.get("PORT", arguments.get("--port", 5019)))
    config = imp.load_source("config", arguments["--config"])
    app.departures_data = DepartureData()
    app.fetcher = Fetcher(config)
    app.run(host='0.0.0.0', port=port, debug=arguments.get("--debug", False))


if __name__ == '__main__':
    main()
