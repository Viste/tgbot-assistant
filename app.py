from flask import Flask, jsonify, request, render_template
from sqlalchemy import delete

from database.manager import Manager
from database.models import Calendar, StreamEmails
from main import session_maker

app = Flask(__name__)
app.env = "production"


@app.route('/')
async def index():
    return render_template('public/index.html')


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
    async with session_maker() as session:
        manager = Manager(session)
        emails = await manager.get_active_emails(StreamEmails)
    return jsonify({"success": True, "emails": emails})


@app.route('/api/stream', methods=['POST'])
async def set_stream():
    data = request.json
    chat_name = data.get('chat_name')
    # Здесь должен быть асинхронный код для установки чата стрима
    return jsonify({"success": True, "message": f"Чат стрима установлен на {chat_name}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)
