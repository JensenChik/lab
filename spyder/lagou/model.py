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

class Job(BaseModel):
    __tablename__ = 'lagou_job'
    id = Column(Integer, primary_key=True)
    company_id = Column(Text)
    company_full_name = Column(Text)
    ad_word = Column(Text)
    position_name = Column(Text)
    work_year = Column(Text)
    education = Column(Text)
    job_nature = Column(Text)
    finance_stage = Column(Text)
    industry_field = Column(Text)
    company_short_name = Column(Text)
    city = Column(Text)
    salary = Column(Text)
    position_id = Column(Text)
    position_advantage = Column(Text)
    district = Column(Text)
    company_label_list = Column(Text)
    approve = Column(Text)
    company_size = Column(Text)
    score = Column(Text)
    format_create_time = Column(Text)
    last_login = Column(Text)
    publisher_id = Column(Text)
    explain = Column(Text)
    plus = Column(Text)
    pc_show = Column(Text)
    app_show = Column(Text)
    deliver = Column(Text)
    grade_description = Column(Text)
    promotion_score_explain = Column(Text)
    first_type = Column(Text)
    second_type = Column(Text)
    position_lables = Column(Text)
    business_zones = Column(Text)
    im_state = Column(Text)
    create_time = Column(Text)
    crawint_time = Column(DateTime)

    def __repr__(self):
        return '[%s]%s' % (self.id, self.company_short_name, self.position_name)

engine = create_engine(DATABASE_URI, pool_recycle=3600, encoding='utf-8')
DBSession = sessionmaker(engine)

if __name__ == '__main__':
    BaseModel.metadata.create_all(engine)
