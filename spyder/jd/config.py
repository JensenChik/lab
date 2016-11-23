# coding=utf-8
import ConfigParser

cf = ConfigParser.ConfigParser()
cf.read('/home/suit/lab/spyder/config.ini')
DATABASE_URI = cf.get('jd', 'sql_conn')
url = cf.get('jd', 'url')
max_iter = int(cf.get('jd', 'max_iter'))
