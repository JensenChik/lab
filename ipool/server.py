# coding=utf-8
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import ConfigParser
import os
import json
from random import choice
from flask import Flask
from flask.ext.script import Manager, Server
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import IP

cf = ConfigParser.ConfigParser()
cf.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini'))
DATABASE_URI = cf.get('param', 'sql_conn')
HEART_BEAT = int(cf.get('param', 'heart_beat'))
POOL_SIZE = int(cf.get('param', 'pool_size'))
PAGE_NUM = int(cf.get('param', 'page_num'))

engine = create_engine(DATABASE_URI, pool_recycle=3600, encoding='utf-8')
DBSession = sessionmaker(engine)

app = Flask(__name__)


@app.route('/')
def get():
    session = DBSession()
    valid_ip = session.query(IP).filter(IP.rank != None).order_by(IP.rank).limit(10).all()
    proxies = None if valid_ip == [] else choice(valid_ip).to_proxy()
    session.close()
    return json.dumps(proxies) if proxies is not None else 'None'


if __name__ == "__main__":
    manager = Manager(app)
    server = Server(host='127.0.0.1', port=13579)
    manager.add_command("runserver", server)
    manager.run()
