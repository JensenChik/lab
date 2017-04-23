# coding=utf-8
import sys
import requests
import json
import time
from datetime import date
import os
import multiprocessing

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from spyder.config import DBSession, HEADER, get_proxy, wow_url
from spyder.config import return_none_when_exception, repeat_while_return_none
from spyder.model import AuctionWare


def get(param):
    time.sleep(1)
    realm, url = param
    proxy = get_proxy()
    req = requests.get(url, proxies=proxy, headers=HEADER, timeout=5)
    if req.status_code != 200: raise Exception('error return code')
    auctions = json.loads(req.content).get('auctions') or []
    print 'get {} data in {} by {} done'.format(realm, url, proxy.get('http'))
    time.sleep(4)
    return [AuctionWare(realm=realm, json=json.dumps(ware, ensure_ascii=False), create_date=date.today())
            for ware in auctions]


if __name__ == '__main__':
    print 'start to get wow auction house data'

    pool = multiprocessing.Pool(processes=4)
    data = reduce(
        lambda x, y: x + y,
        pool.map(
            repeat_while_return_none(return_none_when_exception(get)),
            wow_url.items()
        )
    )
    pool.close()
    pool.join()
    print 'get wow auction house data finish, ware count: {}'.format(len(data))

    print 'start to dump auction house data to mysql'
    session = DBSession()
    session.add_all(data)
    session.commit()
    session.close()
    print 'dump auction house to mysql finish'

    print 'all done'
