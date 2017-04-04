from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Integer

BaseModel = declarative_base()


class IP(BaseModel):
    __tablename__ = 'ip'
    url = Column(String(35), unique=True, primary_key=True)
    update_time = Column(DateTime)
    speed = Column(Integer)

    def to_proxy(self):
        return {
            'http': self.url,
            'https': self.url
        }

    def __repr__(self):
        return '{}\t{}\t{}'.format(self.url, self.update_time, self.speed)


if __name__ == '__main__':
    from config import engine

    BaseModel.metadata.create_all(engine)
