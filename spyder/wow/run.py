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
    fp = open('/tmp/{}/{}'.format(date.today(), realm), 'w')
    map(lambda ware: fp.writelines('{}\n'.format(json.dumps(ware, ensure_ascii=False))), auctions)
    fp.close()
    return len(auctions)


if __name__ == '__main__':
    print 'start to get wow auction house data'
    os.mkdir('/tmp/{}'.format(date.today()))

    pool = multiprocessing.Pool(processes=10)
    count = reduce(
        lambda x, y: x + y,
        pool.map(
            repeat_while_return_none(return_none_when_exception(get)),
            wow_url.items()
        )
    )
    pool.close()
    pool.join()
    print 'get wow auction house data finish, ware count: {}'.format(count)

    print 'start to dump auction house data to mysql'
    session = DBSession()
    for realm, _ in wow_url.items():
        fp = open('/tmp/{}/{}'.format(date.today(), realm))
        data = [AuctionWare(realm=realm, json=line, create_date=date.today()) for line in fp]
        session.add_all(data)
        fp.close()
    session.commit()
    session.close()
    print 'dump auction house to mysql finish'

    print 'all done'
