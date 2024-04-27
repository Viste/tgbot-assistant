from enum import Enum, unique

from sqlalchemy import Column, BigInteger, TIMESTAMP, String, Float, DateTime, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import expression

from database.base import Base


@unique
class MemberStatus(Enum):
    ACTIVE = "active"
    LEFT = "left"
    KICKED = "kicked"


class Calendar(Base):
    __tablename__ = "calendar"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    end_time = Column(TIMESTAMP, unique=True, nullable=False)
    mariadb_engine = "InnoDB"


class StreamEmails(Base):
    __tablename__ = "stream_emails"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stream_id = Column(Integer, nullable=False, unique=True)
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


class Broadcast(Base):
    __tablename__ = 'broadcasts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    video_path = Column(String)
    is_live = Column(Boolean, default=False)
    course = relationship('Course', backref=backref('broadcasts', lazy=True))
    mariadb_engine = "InnoDB"

    def __repr__(self):
        return f'<Broadcast {self.id} for course {self.course.name}>'


class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String)
    short_name = Column(String)
    description = Column(String, nullable=False)
    image_url = Column(String)
    mariadb_engine = "InnoDB"

    def __repr__(self):
        return f'<Course {self.name}>'


class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    telegram_id = Column(String, unique=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String)
    allowed_courses = Column(String,  nullable=False, default='academy')
    is_moderator = Column(Boolean)
    is_admin = Column(Boolean)
    is_banned = Column(Boolean)
    mariadb_engine = "InnoDB"
    

class CourseProgram(Base):
    __tablename__ = 'course_programs'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    course = relationship('Course', backref=backref('programs', lazy=True))


class Homework(Base):
    __tablename__ = 'homeworks'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    course = relationship('Course', backref=backref('homeworks', lazy=True))


class HomeworkSubmission(Base):
    __tablename__ = 'homework_submissions'
    id = Column(Integer, primary_key=True)
    homework_id = Column(Integer, ForeignKey('homeworks.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    file_path = Column(String(255))
    grade = Column(Integer)
    comments = Column(Text)
    homework = relationship('Homework', backref=backref('submissions', lazy=True))
    student = relationship('Customer', backref=backref('submissions', lazy=True))