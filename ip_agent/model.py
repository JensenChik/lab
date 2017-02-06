from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Integer

BaseModel = declarative_base()


class IP(BaseModel):
    __tablename__ = 'ip'
    id = Column(Integer, primary_key=True)
    url = Column(String(35), unique=True)
    create_time = Column(DateTime)
    rank = Column(Integer)

    def to_proxy(self):
        return {
            'http': self.url,
            'https': self.url
        }


if __name__ == '__main__':
    from config import engine

    BaseModel.metadata.create_all(engine)
