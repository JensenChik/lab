# coding=utf-8
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import json
from random import choice
from flask import Flask
from flask.ext.script import Manager, Server
from config import DBSession, host, port
from model import IP

app = Flask(__name__)


@app.route('/')
def get():
    session = DBSession()
    valid_ip = session.query(IP).all()
    proxies = None if valid_ip == [] else choice(valid_ip).to_proxy()
    session.close()
    return json.dumps(proxies) if proxies is not None else 'None'


if __name__ == "__main__":
    manager = Manager(app)
    server = Server(host=host, port=port)
    manager.add_command("runserver", server)
    manager.run()
