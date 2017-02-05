import ConfigParser
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

cf = ConfigParser.ConfigParser()
cf.read(os.path.join(sys.path[0], 'config.ini'))
DATABASE_URI = cf.get('param', 'sql_conn')
HEART_BEAT = int(cf.get('param', 'heart_beat'))
POOL_SIZE = int(cf.get('param', 'pool_size'))
PAGE_NUM = int(cf.get('param', 'page_num'))

engine = create_engine(DATABASE_URI, pool_recycle=3600, encoding='utf-8')
DBSession = sessionmaker(engine)
