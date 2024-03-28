from flask import Flask, request, redirect, url_for, render_template_string, jsonify, render_template, flash
from flask_admin import Admin
from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import delete

from core.helpers.tools import chat_settings, ChatState
from database.manager import Manager
from database.models import Calendar, NeuropunkPro, Zoom, StreamEmails, Admins
from tools.shared import session_maker

app = Flask(__name__, static_folder='public', template_folder='public')
app.secret_key = 'pprfnktechsekta2024'
app.env = "production"
chat_state = ChatState()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated


admin = Admin(app, name='Моя Админка', template_mode='bootstrap3', index_view=MyAdminIndexView(), url='/')

admin.add_view(ModelView(Calendar, session_maker()))
admin.add_view(ModelView(NeuropunkPro, session_maker()))
admin.add_view(ModelView(Zoom, session_maker()))
admin.add_view(ModelView(StreamEmails, session_maker()))


@login_manager.user_loader
def load_user(user_id):
    return Admins.query.get(int(user_id))


@app.route('/')
async def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
async def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Admins.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin.index'))
        else:
            flash('Invalid username or password')
    return render_template_string('''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    ''')


@app.route('/logout')
@login_required
async def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/api/online', methods=['POST'])
async def online():
    async with session_maker() as session:
        dt = request.json.get('end_time')
        new_date = Calendar(end_time=dt)
        session.add(new_date)
        await session.commit()
    return jsonify({"success": True, "message": "Прием демок включен"})


@app.route('/api/offline', methods=['POST'])
async def offline():
    async with session_maker() as session:
        await session.execute(delete(Calendar))
        await session.execute(delete(StreamEmails))
        await session.commit()
    return jsonify({"success": True, "message": "Прием демок выключен"})


@app.route('/api/emails', methods=['GET'])
async def get_emails():
    course_name = request.args.get('course')
    course_models = {
        "np_pro": NeuropunkPro,
        "zoom": Zoom,
    }
    if course_name in course_models:
        async with session_maker() as session:
            manager = Manager(session)
            emails = await manager.get_active_emails(course_models[course_name])
        return jsonify({"success": True, "emails": emails})
    else:
        return jsonify({"success": False, "message": "Неверное имя курса"}), 400


@app.route('/api/stream', methods=['POST'])
async def set_stream():
    data = request.json
    chat_name = data.get('chat_name')
    if chat_name in chat_settings:
        settings = chat_settings[chat_name]
        chat_state.active_chat = settings["active_chat"]
        chat_state.thread_id = settings.get("thread_id")
        return jsonify({"success": True, "message": f"Чат стрима установлен на {chat_name}"})
    else:
        return jsonify({"success": False, "message": "Неверное имя чата"}), 400
