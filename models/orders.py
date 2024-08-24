from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column
import datetime
from database_conf.db_setup import Base


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = mapped_column(ForeignKey("users.id"))
    order_id = Column(String(100), nullable=True)
    order_status = Column(String(10), nullable=True)
    order_made_at = Column(DateTime, default=datetime.datetime.utcnow)