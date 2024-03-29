import flask_admin as admin
import flask_login as login
from flask import Flask, request, redirect, url_for, render_template, flash
from flask_admin import expose, BaseView, helpers
from flask_admin.contrib import rediscli
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from werkzeug.security import check_password_hash
from wtforms import form, fields, validators

from core.helpers.tools import chat_settings, ChatState
from database.models import Calendar, NeuropunkPro, Zoom, StreamEmails, User, Config, ChatMember
from tools.utils import config

app = Flask(__name__, static_folder='public', template_folder='public')
app.config['SECRET_KEY'] = 'pprfnktechsekta2024'
app.config['SQLALCHEMY_DATABASE_URI'] = config.db_string
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.env = "production"
chat_state = ChatState()


class Admins(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    telegram_id: int = db.Column(db.BigInteger, nullable=False, unique=True)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.username


class LoginForm(form.Form):
    login = fields.StringField(validators=[validators.InputRequired()])
    password = fields.PasswordField(validators=[validators.InputRequired()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        if not check_password_hash(user.password_hash, self.password.data):
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db.session.query(Admins).filter_by(username=self.login.data).first()


def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(Admins).get(user_id)


class MyAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('login'))
        return super(MyAdminIndexView, self).index()


class MyModelView(ModelView):
    def is_accessible(self):
        return login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class MyAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super(MyAdminIndexView, self).render('admin/login.html')

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


class OnlineView(BaseView):
    @expose('/', methods=('GET', 'POST'))
    def index(self):
        if request.method == 'POST':
            dt = request.form.get('end_time')
            new_date = Calendar(end_time=dt)
            db.session.add(new_date)
            db.session.commit()
            flash('Время окончания приема демок установлено.')
            return redirect(url_for('.index'))
        return self.render('admin/online_form.html')

    def is_accessible(self):
        return login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


class OfflineView(BaseView):
    @expose('/', methods=('POST',))
    def index(self):
        db.session.query(Calendar).delete()
        db.session.query(StreamEmails).delete()
        db.session.commit()
        flash('Прием демок выключен.')
        return redirect(url_for('.index'))

    def is_accessible(self):
        return login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


class StreamChatView(BaseView):
    @expose('/', methods=('GET', 'POST'))
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
            return redirect(url_for('.index'))
        return self.render('admin/stream_chat_form.html')

    def is_accessible(self):
        return login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


class EmailsView(BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        course_name = request.args.get('course', 'np_pro')
        course_models = {
            "np_pro": NeuropunkPro,
            "zoom": Zoom,
        }
        if course_name in course_models:
            emails = db.session.query(course_models[course_name]).filter_by(active=True).all()
            return self.render('admin/emails_list.html', emails=emails, course_name=course_name)
        else:
            flash('Неверное имя курса', 'error')
            return redirect(url_for('.index'))

    def is_accessible(self):
        return login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


@app.route('/')
def index():
    return render_template('index.html')


init_login()

admin = admin.Admin(app, name='Cyberpaper', index_view=MyAdminIndexView(), base_template='my_master.html', template_mode='bootstrap4', url='/admin')
admin.add_view(OnlineView(name='Включение приема демок', endpoint='online', category='Управление Ботом'))
admin.add_view(OfflineView(name='Выключение приема демок', endpoint='offline', category='Управление Ботом'))
admin.add_view(StreamChatView(name='Управлением Чатом', endpoint='stream_chat', category='Управление Ботом'))
admin.add_view(EmailsView(name='Получение Email c курсов', endpoint='emails', category='Управление Ботом'))

admin.add_view(MyModelView(menu_class_name='Таблица даты окончания приема демок', model=Calendar, session=db.session, category="Управление базой"))
admin.add_view(MyModelView(menu_class_name='Таблица курса Pro по подписке', model=NeuropunkPro, session=db.session, category="Управление базой"))
admin.add_view(MyModelView(menu_class_name='Таблица курса Zoom', model=Zoom, session=db.session, category="Управление базой"))
admin.add_view(MyModelView(menu_class_name='Таблица с эмейлами', model=StreamEmails, session=db.session, category="Управление базой"))
admin.add_view(MyModelView(menu_class_name='Таблица c админами', model=Admins, session=db.session, category="Управление базой"))
admin.add_view(MyModelView(menu_class_name='Таблица конфига', model=Config, session=db.session, category="Управление базой"))
admin.add_view(MyModelView(menu_class_name='Таблица подписок на приват', model=User, session=db.session, category="Управление базой"))
admin.add_view(MyModelView(menu_class_name='Таблица всех пользователей', model=ChatMember, session=db.session, category="Управление базой"))
admin.add_view(rediscli.RedisCli(Redis()))
admin.add_link(MenuLink(name='Logout', url='/logout'))
