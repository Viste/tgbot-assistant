import logging
import os

import flask_admin as admin
from flask import Flask, request, redirect, url_for, render_template, flash, send_from_directory, jsonify, session
from flask_admin import expose, BaseView, helpers, Admin
from flask_admin.contrib import rediscli
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_admin.menu import MenuLink
from flask_login import logout_user, current_user, login_required, LoginManager, login_user
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from werkzeug.security import check_password_hash
from wtforms import form, fields, validators

from core.helpers.tools import chat_settings, ChatState, MessageProcessor
from database.models import NeuropunkPro, Zoom, User, Config
from tools.utils import config

logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='public', template_folder='public')
app.config['SECRET_KEY'] = 'pprfnktechsekta2024'
app.config['SQLALCHEMY_DATABASE_URI'] = config.db_string
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 5
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
db = SQLAlchemy(app)
app.env = "production"
chat_state = ChatState()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    user = Admins.query.get(int(user_id))
    print(user)
    return user


class Broadcast(db.Model):
    __tablename__ = 'broadcasts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    video_path = db.Column(db.String)
    is_live = db.Column(db.Boolean, default=False)
    course = db.relationship('Course', backref=db.backref('broadcasts', lazy=True))
    mariadb_engine = "InnoDB"

    def __repr__(self):
        return f'<Broadcast {self.id} for course {self.course.name}>'


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    name = db.Column(db.String)
    short_name = db.Column(db.String)
    image_url = db.Column(db.String)
    description = db.Column(db.String, nullable=False)
    mariadb_engine = "InnoDB"

    def __repr__(self):
        return f'<Course {self.name}>'


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    telegram_id = db.Column(db.String, unique=True)
    username = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String)
    allowed_courses = db.Column(db.String, nullable=False, default='academy')
    is_moderator = db.Column(db.Boolean)
    is_admin = db.Column(db.Boolean)
    is_banned = db.Column(db.Boolean)
    mariadb_engine = "InnoDB"

    def is_authenticated(self):
        if not self.is_admin:
            return True
        else:
            return False

    @property
    def is_active(self):
        # пользователь активен, если он не забанен.
        return self.is_admin

    @property
    def is_anonymous(self):
        # должно возвращать False, так как пользователи не анонимны.
        return False

    def get_id(self):
        # Возвращаем уникальный идентификатор пользователя в виде строки для управления пользовательской сессией.
        return str(self.id)


class Admins(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    telegram_id: int = db.Column(db.BigInteger, nullable=False, unique=True)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    mariadb_engine = "InnoDB"

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        # пользователь активен, если он не забанен.
        return self.is_admin

    @property
    def is_anonymous(self):
        # должно возвращать False, так как пользователи не анонимны.
        return False

    def get_id(self):
        # Возвращаем уникальный идентификатор пользователя в виде строки для управления пользовательской сессией.
        return str(self.id)


class LoginForm(form.Form):
    login = fields.StringField(validators=[validators.InputRequired()])
    password = fields.PasswordField(validators=[validators.InputRequired()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Вы не зарегистрированы')

        if not check_password_hash(user.password_hash, self.password.data):
            raise validators.ValidationError('Неправильный Пароль')

        if user.is_admin is False:
            raise validators.ValidationError('Вы не администратор')

    def get_user(self):
        return db.session.query(Admins).filter_by(username=self.login.data).first()


class MyAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login_user(user)

        if current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super(MyAdminIndexView, self).render('admin/login.html')

    @expose('/logout/')
    def logout_view(self):
        logout_user()
        session.clear()
        return redirect(url_for('.login_view'))


class MyModelView(ModelView):
    form_base_class = SecureForm

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


class StreamChatView(BaseView):
    @expose('/', methods=('GET', 'POST'))
    @login_required
    def index(self):
        if request.method == 'POST':
            chat_name = request.form.get('chat_name')
            if chat_name in chat_settings:
                settings = chat_settings[chat_name]
                chat_state.active_chat = settings["active_chat"]
                chat_state.thread_id = settings.get("thread_id")
                flash(f'Чат стрима установлен на {chat_name}.')
            else:
                flash('Неверное имя чата.')
            return redirect(url_for('admin.index'))
        return self.render('admin/stream_chat_form.html')

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


class EmailsView(BaseView):
    @expose('/', methods=['GET'])
    @login_required
    def index(self):
        course_name = request.args.get('course', 'np_pro')
        course_models = {
            "np_pro": NeuropunkPro,
            "zoom": Zoom,
        }
        emails = []
        if course_name in course_models:
            emails = db.session.query(course_models[course_name]).all()
            return self.render('admin/emails_list.html', emails=emails, course_name=course_name)
        else:
            flash('Неверное имя курса', 'error')
            return redirect(url_for('admin.index'))

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/messages', methods=['GET'])
def obs():
    messages = MessageProcessor.get_messages()
    logger.info('response info: %s %s %s', request.remote_addr, request.url, request.headers.get('User-Agent'))
    return jsonify(messages), 200


@app.route('/chat', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'chat.html')


@app.route('/chat_admin', methods=['GET'])
def admin():
    return send_from_directory(app.static_folder, 'chat_admin.html')


@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    key = request.form.get('key')

    if key != 'sharkubiseichas':
        return jsonify({'status': 'Invalid admin key'}), 401

    MessageProcessor.clear_messages()
    return jsonify({'status': 'Chat cleared'}), 200


my_redis = Redis(host=config.redis.host, port=config.redis.port, db=config.redis.db)

admin_panel = Admin(app, name='Cyberpaper', index_view=MyAdminIndexView(), base_template='admin/my_master.html', template_mode='bootstrap4', url='/admin')

admin_panel.add_view(StreamChatView(name='Управлением Чатом', endpoint='stream_chat', category='Управление Ботом'))
admin_panel.add_view(EmailsView(name='Получение Email c курсов', endpoint='emails', category='Управление Ботом'))

admin_panel.add_view(MyModelView(menu_class_name='Таблица курса Pro по подписке', model=NeuropunkPro, session=db.session, category="Управление базой"))
admin_panel.add_view(MyModelView(menu_class_name='Таблица курса Zoom', model=Zoom, session=db.session, category="Управление базой"))
admin_panel.add_view(MyModelView(menu_class_name='Таблица c админами', model=Admins, session=db.session, category="Управление базой"))
admin_panel.add_view(MyModelView(menu_class_name='Таблица конфига', model=Config, session=db.session, category="Управление базой"))
admin_panel.add_view(MyModelView(menu_class_name='Таблица подписок на приват', model=User, session=db.session, category="Управление базой"))
admin_panel.add_view(MyModelView(menu_class_name='Таблица курсов', model=Course, session=db.session, category="Управление базой"))
admin_panel.add_view(MyModelView(menu_class_name='Таблица пользователей с курсов', model=Customer, session=db.session, category="Управление базой"))
admin_panel.add_view(MyModelView(menu_class_name='Таблица трансляций с курсов', model=Broadcast, session=db.session, category="Управление базой"))
admin_panel.add_view(rediscli.RedisCli(Redis(my_redis)))
admin_panel.add_link(MenuLink(name='Logout', url='/logout'))
