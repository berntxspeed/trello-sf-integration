import os

from flask import Flask
from flask_script import Manager
from flask_script import Server
from flask_script import Shell

from server import app

manager = Manager(app)

def make_shell_context():
    return {
        'app': app
    }

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('runserver', Server(host='0.0.0.0', port=5000))

if __name__ == '__main__':
    manager.run()
