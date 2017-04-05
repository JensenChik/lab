# coding=utf-8
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import ConfigParser
import json
import os
import logging
import requests

reload(sys)
sys.setdefaultencoding('utf-8')

cf = ConfigParser.ConfigParser()
cf.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini'))

# 基本配置
DATABASE_URI = cf.get('base', 'db_uri')
POOL_URL = cf.get('base', 'pool_url')
HEADER = json.loads(cf.get('base', 'header'))
engine = create_engine(DATABASE_URI, pool_recycle=3600, encoding='utf-8')
DBSession = sessionmaker(engine)
logging.basicConfig(
    level=logging.WARNING,
    format='[%(levelname)s]\t%(asctime)s\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()


def get_proxy():
    proxy = requests.get(POOL_URL).content
    return None if proxy == 'None' else json.loads(proxy)


class return_none_when_exception:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        try:
            result = self.func(*args, **kwargs)
        except Exception:
            result = None
        return result


class repeat_while_return_none:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        result = self.func(*args, **kwargs)
        while result is None:
            result = self.func(*args, **kwargs)
        return result


# 京东配置
JD_url = cf.get('jd', 'url')
JD_max_iter = int(cf.get('jd', 'max_iter'))

# 拉勾配置
lagou_company_url = cf.get('lagou', 'company_url')
lagou_job_url = cf.get('lagou', 'company_url')
lagou_max_iter = int(cf.get('lagou', 'max_iter'))
lagou_city_json = json.loads(cf.get('lagou', 'city_json'))
lagou_stage_json = json.loads(cf.get('lagou', 'stage_json'))
lagou_domain_json = json.loads(cf.get('lagou', 'domain_json'))

# 汽车之家配置
autohome_car_url = cf.get('autohome', 'car_url')
autohome_max_iter = int(cf.get('autohome', 'max_iter'))
autohome_brand_json = json.loads(cf.get('autohome', 'brand_json'))
