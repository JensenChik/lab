from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Text, DateTime, Integer

BaseModel = declarative_base()


class JDWare(BaseModel):
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


class LagouCompany(BaseModel):
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


class LagouJob(BaseModel):
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
        return '[%s]%s' % (self.id, self.company_short_name)


class AutoHomeCar(BaseModel):
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


if __name__ == '__main__':
    from config import engine
    BaseModel.metadata.create_all(engine)
