from flask import Flask, jsonify, request, render_template
from sqlalchemy import delete

from core.helpers.tools import chat_settings, ChatState
from database.manager import Manager
from database.models import Calendar, NeuropunkPro, Zoom
from main import session_maker

app = Flask(__name__, static_folder='public', template_folder='public')
app.env = "production"
chat_state = ChatState()


@app.route('/')
async def index():
    return render_template('index.html')


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
