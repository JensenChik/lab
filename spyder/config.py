# coding=utf-8
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import ConfigParser
import json
import os
import logging

reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('..')
from ip_agent import Consumer

cf = ConfigParser.ConfigParser()
cf.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini'))

# 基本配置
DATABASE_URI = cf.get('base', 'sql_uri')
engine = create_engine(DATABASE_URI, pool_recycle=3600, encoding='utf-8')
DBSession = sessionmaker(engine)
logging.basicConfig(
    level=logging.WARNING,
    format='[%(levelname)s]\t%(asctime)s\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()
ip_pool = Consumer()

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
