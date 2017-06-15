import os
import sys
import logging
from flask import Flask
import requests

try:
    config = {
        'sfapi_consumer_key': os.environ.get('SFAPI_CONSUMER_KEY'),
        'sfapi_consumer_secret': os.environ.get('SFAPI_CONSUMER_SECRET'),
        'enable_verbose_logging': os.environ.get('ENABLE_VERBOSE_LOGGING', None),
        'database_url': os.environ.get('DATABASE_URL')
    }
    if config['enable_verbose_logging'] is not None:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
except Exception as e:
    print('missing an environment variable: ' + repr(e))
    raise

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'
