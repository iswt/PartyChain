import os
from flask import Flask

from flask.ext.socketio import SocketIO

app = Flask(__name__)
app.config.from_object('config')

socketio = SocketIO(app)

from app import routes
