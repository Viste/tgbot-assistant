from enum import Enum, unique

from flask_login import UserMixin
from sqlalchemy import Column, BigInteger, TIMESTAMP, String, Float, DateTime, Integer, Boolean, Text
from sqlalchemy.sql import expression
from werkzeug.security import generate_password_hash, check_password_hash

from database.base import Base


@unique
class MemberStatus(Enum):
    ACTIVE = "active"
    LEFT = "left"
    KICKED = "kicked"


class Admins(Base, UserMixin):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    telegram_id: int = Column(BigInteger, nullable=False, unique=True)
    password_hash = Column(String(256))
    is_admin = Column(Boolean, default=False)
    mariadb_engine = "InnoDB"

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, unique=True)
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

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=False, unique=True)
    telegram_username = Column(String(255), nullable=True, unique=True)
    email = Column(String(255), nullable=True)
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    subscription_status = Column(String(50), nullable=False, default='inactive')
    mariadb_engine = "InnoDB"


class ChatMember(Base):
    __tablename__ = "chat_members"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=False)
    telegram_username = Column(String(255), nullable=True)
    chat_name = Column(String(255), nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    status = Column(String(50), nullable=False, default='active')
    banned = Column(Boolean, default=False, server_default=expression.false())
    mariadb_engine = "InnoDB"


class Config(Base):
    __tablename__ = 'config'
    id = Column(Integer, primary_key=True, autoincrement=True)
    key_name = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    mariadb_engine = "InnoDB"


class Zoom(Base):
    __tablename__ = "zoom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=False, unique=True)
    telegram_username = Column(String(255), nullable=True, unique=True)
    email = Column(String(255), nullable=True)
    mariadb_engine = "InnoDB"