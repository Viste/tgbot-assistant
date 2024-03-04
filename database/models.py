from sqlalchemy import Column, BigInteger, TIMESTAMP, String, Float, DateTime, Integer, UniqueConstraint

from database.base import Base


class Calendar(Base):
    __tablename__ = "calendar"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    end_time = Column(TIMESTAMP, unique=True, nullable=False)
    mariadb_engine = "InnoDB"


class StreamEmails(Base):
    __tablename__ = "stream_emails"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stream_id = Column(Integer, nullable=False, autoincrement=False, unique=True)
    email = Column(String(255), nullable=False, unique=False)
    mariadb_engine = "InnoDB"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    telegram_id: int = Column(BigInteger, nullable=False, unique=True)
    telegram_username = Column(String(255), nullable=True, unique=True)
    balance_amount = Column(Float, nullable=False, default=0)
    used_tokens = Column(Integer, nullable=False, default=0)
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    subscription_status = Column(String(50), nullable=False, default='inactive')
    mariadb_engine = "InnoDB"


class NeuropunkPro(Base):
    __tablename__ = "neuropunk_pro"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    telegram_id = Column(BigInteger, nullable=False, unique=True)
    telegram_username = Column(String(255), nullable=True, unique=True)
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    subscription_status = Column(String(50), nullable=False, default='inactive')
    mariadb_engine = "InnoDB"
