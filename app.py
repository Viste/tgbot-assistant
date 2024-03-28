import asyncio

from flask import Flask, request, redirect, url_for, render_template, flash
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_login import LoginManager, login_user, logout_user, current_user
from sqlalchemy import delete
from wtforms import form, fields, validators

from core.helpers.tools import chat_settings, ChatState
from database.manager import Manager
from database.models import Calendar, NeuropunkPro, Zoom, StreamEmails, Admins
from tools.shared import session_maker

app = Flask(__name__, static_folder='public', template_folder='public')
app.secret_key = 'pprfnktechsekta2024'
app.env = "production"
chat_state = ChatState()
login_manager = LoginManager()
login_manager.login_view = 'login'


class OnlineView(BaseView):
    @expose('/', methods=('GET', 'POST'))
    def index(self):
        if request.method == 'POST':
            dt = request.form.get('end_time')
            with session_maker() as session:
                new_date = Calendar(end_time=dt)
                session.add(new_date)
                session.commit()
            flash('Время окончания приема демок установлено.')
            return redirect(url_for('.index'))
        return self.render('admin/online_form.html')


class OfflineView(BaseView):
    @expose('/', methods=('POST',))
    def index(self):
        with session_maker() as session:
            session.execute(delete(Calendar))
            session.execute(delete(StreamEmails))
            session.commit()
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
            with session_maker() as session:
                manager = Manager(session)
                emails = manager.get_active_emails(course_models[course_name])
        else:
            flash('Неверное имя курса', 'error')
            return redirect(url_for('.index'))
        return self.render('admin/emails_list.html', emails=emails, course_name=course_name)


class LoginForm(form.Form):
    username = fields.StringField(validators=[validators.InputRequired()])
    password = fields.PasswordField(validators=[validators.InputRequired()])

    async def validate_login(self):
        async with session_maker() as session:
            manager = Manager(session)
            valid, user = await manager.check_user_credentials(self.username.data, self.password.data)
            return valid, user


class RegistrationForm(form.Form):
    username = fields.StringField(validators=[validators.InputRequired()])
    password = fields.PasswordField(validators=[validators.InputRequired()])

    async def validate_username(self, field):
        async with session_maker() as session:
            manager = Manager(session)
            user_exists = await manager.check_user_exists(field.data)
            if user_exists:
                raise validators.ValidationError('Duplicate username')


async def init_login(application):
    login_manager.init_app(application)

    @login_manager.user_loader
    async def load_user(user_id):
        async def get_user():
            async with session_maker() as session:
                manager = Manager(session)
                return await manager.get_user_by_id(int(user_id))
        return asyncio.run(get_user())


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return super(MyAdminIndexView, self).index()


class MyModelView(ModelView):
    def is_accessible(self):
        return login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    async def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    async def login_view(self):
        form = LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            async with session_maker() as session:
                manager = Manager(session)
                valid, user = await manager.check_user_credentials(username, password)
                if valid:
                    login_user(user)
                    return redirect(url_for('.index'))
                else:
                    flash('Invalid username or password')
        link = '<p>Don\'t have an account? <a href="' + url_for('.register_view') + '">Click here to register.</a></p>'
        return self.render('admin/login.html', form=form, link=link)

    @expose('/logout/')
    async def logout_view(self):
        logout_user()
        return redirect(url_for('.index'))


@app.route('/')
def index():
    return render_template('index.html')


init_login(app)

admin = Admin(app, name='Моя Админка', template_mode='bootstrap3', index_view=MyAdminIndexView(), url='/admin')

admin.add_view(ModelView(Calendar, session_maker()))
admin.add_view(ModelView(NeuropunkPro, session_maker()))
admin.add_view(ModelView(Zoom, session_maker()))
admin.add_view(ModelView(StreamEmails, session_maker()))
admin.add_view(ModelView(Admins, session_maker()))
admin.add_view(OnlineView(name='Online', endpoint='online'))
admin.add_view(OfflineView(name='Offline', endpoint='offline'))
admin.add_view(StreamChatView(name='Stream Chat', endpoint='stream_chat'))
admin.add_view(EmailsView(name='Emails', endpoint='emails'))
admin.add_link(MenuLink(name='Logout', url='/logout'))