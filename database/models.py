from datetime import datetime
from sqlalchemy import Column, BigInteger, TIMESTAMP, String, Float, DateTime, Integer

from database.base import Base


class Calendar(Base):
    __tablename__ = "calendar"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    end_time = Column(TIMESTAMP, unique=True, nullable=False)
    mariadb_engine = "InnoDB"


class StreamEmails(Base):
    __tablename__ = "stream_emails"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stream_id = Column(Integer, nullable=False, autoincrement=False, unique=False)
    email = Column(String(255), nullable=False, unique=True)
    mariadb_engine = "InnoDB"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    telegram_id = Column(BigInteger, nullable=False, unique=True)
    telegram_username = Column(String(255), nullable=True, unique=True)
    balance_amount = Column(Float, nullable=False, default=0)
    max_tokens = Column(Integer, nullable=False, default=0)
    current_tokens = Column(Integer, nullable=False, default=0)
    price_per_token = Column(Float, nullable=False, default=0.002)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    subscription_status = Column(String(50), nullable=False, default='inactive')
    mariadb_engine = "InnoDB"
