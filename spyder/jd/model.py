# coding=utf-8
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Text, DateTime, Integer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URI

BaseModel = declarative_base()


class Ware(BaseModel):
    __tablename__ = 'jd_ware'
    id = Column(Integer, primary_key=True)
    key_word = Column(Text)
    ware_id = Column(Text)
    name = Column(Text)
    price = Column(Text)
    diff_mobile_price = Column(Text)
    is_self = Column(Text)
    shop_name = Column(Text)
    stock_state = Column(Text)
    available_in_store = Column(Text)
    pre_sale = Column(Text)
    total_count = Column(Text)
    good = Column(Text)
    sams_tag = Column(Text)
    sams_price = Column(Text)
    eBook_flag = Column(Text)
    can_free_read = Column(Text)
    promotion_flag = Column(Text)
    m_promotion_id = Column(Text)
    is_booking = Column(Text)
    dis_price = Column(Text)
    cid1 = Column(Text)
    cid2 = Column(Text)
    cat_id = Column(Text)
    up_to_saving = Column(Text)
    eche = Column(Text)
    author = Column(Text)
    priority = Column(Text)
    international = Column(Text)
    stock_quantity = Column(Text)
    adword = Column(Text)
    lowest_buy = Column(Text)
    create_time = Column(DateTime)

    def __repr__(self):
        return '[%s]%s' % (self.id, self.name)


engine = create_engine(DATABASE_URI, pool_recycle=3600, encoding='utf-8')
DBSession = sessionmaker(engine)

if __name__ == '__main__':
    BaseModel.metadata.drop_all(engine)
    BaseModel.metadata.create_all(engine)