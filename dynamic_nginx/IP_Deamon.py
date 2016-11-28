# coding=utf-8
from Router import Router
import time
import logging
import commands

logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s\t%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename='ipchange.log',
        filemode='w'
)

router = Router('TPLINK_WR842N', passwd="WaQ7x7448oefbwK")
ip4nginx = now_valid_ip = None
while True:
    if router.is_private_ip():
        logging.error('ip(%s) is private ip, now to reconnect.' % router.get_ip())
        router.reconnect()
    else:
        now_valid_ip = router.get_ip()

    if now_valid_ip != ip4nginx:
        logging.warning('update nginx(%s) to new valid ip(%s)' % (ip4nginx, now_valid_ip))
        status, info = commands.getstatusoutput("ssh root@nazgrim.com 'cd /home/env; python reload_nginx.py %s'" % now_valid_ip)
        if status == 0:
            logging.warning('nginx proxy ip now changed')
            ip4nginx = now_valid_ip
        else:
            logging.error('nginx proxy ip change failed')
    elif not router.is_private_ip():
        logging.warning('ip(%s) unchange' % router.get_ip())

    time.sleep(30)
