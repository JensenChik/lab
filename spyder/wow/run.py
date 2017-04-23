# coding=utf-8
import sys
import requests
import json
import time
from datetime import date
import os
import shutil
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
    print 'get {} data by {} done'.format(realm, proxy.get('http'))
    time.sleep(4)
    fp = open('/tmp/{}/{}'.format(date.today(), realm), 'w')
    map(lambda ware: fp.writelines('{}\n'.format(json.dumps(ware, ensure_ascii=False))), auctions)
    fp.close()
    return len(auctions)


if __name__ == '__main__':
    print 'start to clean env'
    path = '/tmp/{}'.format(date.today())
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)

    print 'start to get wow auction house data'
    pool = multiprocessing.Pool(processes=20)
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

    print 'start to clean mysql dirty data'
    session = DBSession()
    session.delete(AuctionWare).filter_by(create_date=date.today())
    session.commit()
    session.close()

    print 'start to dump auction house data to mysql'
    for realm in wow_url.keys():
        session = DBSession()
        fp = open('/tmp/{}/{}'.format(date.today(), realm))
        data = [AuctionWare(realm=realm, json=line, create_date=date.today()) for line in fp]
        session.add_all(data)
        fp.close()
        print 'dump {} to mysql finish'.format(realm)
        session.commit()
        session.close()
    print 'dump auction house to mysql finish'

    print 'finally, clean env'
    shutil.rmtree(path)
    print 'all done'
