import flask_admin as admin
import flask_login as login
from flask import Flask, request, redirect, url_for, render_template, flash
from flask_admin import AdminIndexView, expose, BaseView, helpers
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import form, fields, validators

from core.helpers.tools import chat_settings, ChatState
from database.models import Calendar, NeuropunkPro, Zoom, StreamEmails
from tools.utils import config

app = Flask(__name__, static_folder='public', template_folder='public')
app.config['SECRET_KEY'] = 'pprfnktechsekta2024'
app.config['SQLALCHEMY_DATABASE_URI'] = config.db_url
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


def check_user_credentials(username: str, password: str) -> bool:
    user = db.session.query(Admins).filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return True
    return False


def get_user_by_username(username: str) -> Admins:
    return db.session.query(Admins).filter_by(username=username).first()


def get_user_by_id(user_id: int) -> Admins:
    return db.session.query(Admins).get(user_id)


def check_user_exists(username: str) -> bool:
    user = db.session.query(Admins).filter_by(username=username).first()
    return user is not None


class LoginForm(form.Form):
    username = fields.StringField(validators=[validators.InputRequired()])
    password = fields.PasswordField(validators=[validators.InputRequired()])

    def validate_login(self):
        valid, user = check_user_credentials(self.username.data, self.password.data)
        return valid, user


class RegistrationForm(form.Form):
    username = fields.StringField(validators=[validators.InputRequired()])
    password = fields.PasswordField(validators=[validators.InputRequired()])

    @staticmethod
    def validate_username(field):
        user_exists = check_user_exists(field.data)
        if user_exists:
            raise validators.ValidationError('Duplicate username')


def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        def get_user():
            return get_user_by_id(int(user_id))
        return get_user()


class MyAdminIndexView(AdminIndexView):
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
    async def login_view(self):
        form = LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            valid, user = check_user_credentials(username, password)
            if valid:
                login.login_user(user)
                return redirect(url_for('.index'))
            else:
                flash('Invalid username or password')
        link = '<p>Don\'t have an account? <a href="' + url_for('.register_view') + '">Click here to register.</a></p>'
        return self.render('admin/login.html', form=form, link=link)

    @expose('/register/', methods=('GET', 'POST'))
    def register_view(self):
        form = RegistrationForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = Admins()

            form.populate_obj(user)
            # we hash the users password to avoid saving it as plaintext in the db,
            # remove to use plain text:
            user.password = generate_password_hash(form.password.data)

            db.session.add(user)
            db.session.commit()

            login.login_user(user)
            return redirect(url_for('.index'))
        link = '<p>Already have an account? <a href="' + url_for('.login_view') + '">Click here to log in.</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        return super(MyAdminIndexView, self).index()

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

class OfflineView(BaseView):
    @expose('/', methods=('POST',))
    def index(self):
        db.session.query(Calendar).delete()
        db.session.query(StreamEmails).delete()
        db.session.commit()
        flash('Прием демок выключен.')
        return redirect(url_for('admin.index'))


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


class EmailsView(BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        course_name = request.args.get('course')
        course_models = {
            "np_pro": NeuropunkPro,
            "zoom": Zoom,
        }
        emails = []
        if course_name in course_models:
            emails = db.session.query(course_models[course_name]).filter_by(active=True).all()
        else:
            flash('Неверное имя курса', 'error')
            return redirect(url_for('.index'))
        return self.render('admin/emails_list.html', emails=emails, course_name=course_name)


@app.route('/')
def index():
    return render_template('index.html')


init_login()

admin = admin.Admin(app, name='Админка Cyberpaper', template_mode='bootstrap4', index_view=MyAdminIndexView(), url='/admin')
admin.add_view(ModelView(Calendar, db.session))
admin.add_view(ModelView(NeuropunkPro, db.session))
admin.add_view(ModelView(Zoom, db.session))
admin.add_view(ModelView(StreamEmails, db.session))
admin.add_view(ModelView(Admins, db.session))
admin.add_view(OnlineView(name='Online', endpoint='online'))
admin.add_view(OfflineView(name='Offline', endpoint='offline'))
admin.add_view(StreamChatView(name='Stream Chat', endpoint='stream_chat'))
admin.add_view(EmailsView(name='Emails', endpoint='emails'))
admin.add_link(MenuLink(name='Logout', url='/logout'))
