web: gunicorn manage:app -b 0.0.0.0:$PORT --log-file=-
worker: lein run -m manage:worker
