Client for HSL realtime data
============================

This is only compatible with Python2, as `suds` does not support Python3. `suds-py3` fork seems to be broken.

Usage:

```
virtualenv env
source env/bin/activate
pip install -r requirements.txt
PORT=5005 python service.py &  # starts webserver on port 5005
curl http://localhost:5005/  # outputs JSON describing the API
python fetch_realtime.py -h  # prints out usage
python fetch_realtime.py single-run --config=config.py.example  # fetches and publishes departures information to redis pubsub
```

Settings
--------

Copy `config.py.example` to `config.py` and edit whatever lines, stops and settings you need. See `config.py.example` for detailed documentation and different options.
