# coding=utf-8
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Text, DateTime, Integer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URI

BaseModel = declarative_base()


class Car(BaseModel):
    __tablename__ = 'autohome_car'
    id = Column(Integer, primary_key=True)
    car_id = Column(Integer)
    brand_name = Column(Text)
    series_name = Column(Text)
    car_name = Column(Text)
    min_price = Column(Integer)
    max_price = Column(Integer)
    create_time = Column(DateTime)

    def __repr__(self):
        return '[%s]%s' % (self.id, self.card_name)

engine = create_engine(DATABASE_URI, pool_recycle=3600, encoding='utf-8')
DBSession = sessionmaker(engine)

if __name__ == '__main__':
    BaseModel.metadata.create_all(engine)
