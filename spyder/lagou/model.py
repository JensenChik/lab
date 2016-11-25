# coding=utf-8
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Text, DateTime, Integer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URI

BaseModel = declarative_base()


class Company(BaseModel):
    __tablename__ = 'lagou_company'
    id = Column(Integer, primary_key=True)
    company_id = Column(Text)
    company_full_name = Column(Text)
    company_short_name = Column(Text)
    city = Column(Text)
    position_num = Column(Text)
    city_score = Column(Text)
    finance_stage = Column(Text)
    industry_field = Column(Text)
    country_score = Column(Text)
    company_features = Column(Text)
    process_rate = Column(Text)
    interview_remark_num = Column(Text)
    approve = Column(Text)
    create_time = Column(DateTime)

    def __repr__(self):
        return '[%s]%s' % (self.id, self.company_short_name)

engine = create_engine(DATABASE_URI, pool_recycle=3600, encoding='utf-8')
DBSession = sessionmaker(engine)

if __name__ == '__main__':
    BaseModel.metadata.create_all(engine)
