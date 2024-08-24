from sqlalchemy import Column, Integer, String, DateTime
import datetime
from database_conf.db_setup import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True,autoincrement=True)
    email = Column(String(30), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    first_name = Column(String(20), nullable=True)
    last_name = Column(String(20), nullable=True)
    phone_number = Column(String(15), nullable=True)
    current_role = Column(String(30), nullable=True)
    specialisation = Column(String(30), nullable=True)
    country = Column(String(60), nullable=True, default="not-passed")
    access_token= Column(String(300), nullable=True)
    refresh_token= Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # convert the user data into dict 
    def row2dict(self, row):
        d = {}
        for column in row.__table__.columns:
            if getattr(row, column.name) is not None and column.name != "password":
                d[column.name] = str(getattr(row, column.name))

        return d