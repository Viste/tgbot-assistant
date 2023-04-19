from sqlalchemy import Column, Integer, TIMESTAMP, String

from database.base import Base


class Calendar(Base):
    __tablename__ = "calendar"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False, unique=True)
    end_time = Column(TIMESTAMP, unique=True, nullable=False)
    mariadb_engine = "InnoDB"


class StreamEmails(Base):
    __tablename__ = "streamemails"

    stream_id = Column(Integer, nullable=False, primary_key=True, index=True, autoincrement=False, unique=False)
    email = Column(String(255), nullable=False)
    mariadb_engine = "InnoDB"
