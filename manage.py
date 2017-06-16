import os

from flask import Flask
from flask_script import Manager
from flask_script import Server
from flask_script import Shell
from threading import Thread
import time
import schedule

from server import app, refresh_trello

def run_schedule():
    while 1:
        schedule.run_pending()
        time.sleep(1)

manager = Manager(app)

def make_shell_context():
    return {
        'app': app
    }
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('runserver', Server(host='0.0.0.0', port=5000))

def worker():
    schedule.every(5).minutes.do(refresh_trello)
    t = Thread(target=run_schedule)
    t.start()
    print('starting thread for updating trello')

if __name__ == '__main__':
    manager.run()
