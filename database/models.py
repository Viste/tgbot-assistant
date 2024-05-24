from datetime import datetime
from enum import Enum, unique

from sqlalchemy import Column, BigInteger, String, Float, DateTime, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship, backref

from database.base import Base


@unique
class MemberStatus(Enum):
    ACTIVE = "active"
    LEFT = "left"
    KICKED = "kicked"


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

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    course_id = Column(BigInteger, ForeignKey('courses.id'), nullable=False)
    video_path = Column(String(255))
    is_live = Column(Boolean, default=False)
    title = Column(String(255))
    course = relationship('Course', backref=backref('broadcasts', lazy=True))

    def __repr__(self):
        return f'<Broadcast {self.id} for course {self.course.name}>'


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    telegram_id = Column(String(255), unique=True)
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255))
    allowed_courses = Column(String(255), nullable=False, default='academy')
    is_moderator = Column(Boolean)
    is_admin = Column(Boolean)
    is_banned = Column(Boolean)
    is_podpivas = Column(Boolean, default=False, nullable=False)
    avatar_url = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    headphones = Column(String(255), nullable=True)
    sound_card = Column(String(255), nullable=True)
    pc_setup = Column(Text, nullable=True)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return not self.is_banned

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


class Course(Base):
    __tablename__ = 'courses'

    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True)
    name = Column(String(255))
    short_name = Column(String(255))
    description = Column(Text, nullable=False)
    image_url = Column(String(255))
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    students = relationship('Customer', secondary='course_registrations', back_populates='courses')

    def __repr__(self):
        return f'<Course {self.name}>'


class CourseRegistration(Base):
    __tablename__ = 'course_registrations'

    course_id = Column(BigInteger, ForeignKey('courses.id'), primary_key=True)
    customer_id = Column(BigInteger, ForeignKey('customers.id'), primary_key=True)
    registration_date = Column(DateTime, default=datetime.utcnow)


Customer.courses = relationship('Course', secondary='course_registrations', back_populates='students')


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