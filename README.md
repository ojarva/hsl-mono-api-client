# Client for HSL realtime data

```
pip install -r requirements.txt
PORT=5005 python service.py # start webserver on port 5005
curl http://localhost:5005/ # output JSON describing the API
python fetch_realtime.py # fetches and publishes departures information to redis pubsub
```

Edit `local_settings.py` with your own lines and stops. For stop numbers, 
[this](http://aikataulut.reittiopas.fi/pysakit/en/) is useful. Search using 
"Stops", open stop information and copy ID from the URL (something like 1121601), 
or from the bottom of the page ("Stop ID:"). Stop number displayed next to stop 
name (for example, 0017) is not the ID you need.
