from random import choice
from model import IP
from config import DBSession


class Consumer:
    def __init__(self):
        self._batch_size = 20

    def gen_proxies(self):
        session = DBSession()
        valid_ip = session.query(IP).filter(IP.rank != None).order_by(IP.rank).limit(self._batch_size).all()
        proxies = None if valid_ip == [] else choice(valid_ip).to_proxy()
        session.close()
        return proxies
