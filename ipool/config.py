import ConfigParser
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

cf = ConfigParser.ConfigParser()
cf.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ipool.ini'))

DATABASE_URI = cf.get('db', 'uri')
engine = create_engine(DATABASE_URI, pool_recycle=3600, encoding='utf-8')
DBSession = sessionmaker(engine)

host = cf.get('ipoolserver', 'host')
port = cf.get('ipoolserver', 'port')


def return_none_when_exception(func):
    def _return_none_when_exception(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception:
            result = None
        return result

    return _return_none_when_exception


def repeat_while_return_none(func):
    def _repeat_while_return_none(*args, **kwargs):
        result = func(*args, **kwargs)
        while result is None:
            result = func(*args, **kwargs)
        return result

    return _repeat_while_return_none
