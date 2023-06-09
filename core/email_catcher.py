import logging
from datetime import datetime

from aiogram import types, Router, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from database.models import Calendar, StreamEmails
from tools.states import Mail
from tools.utils import config, check, email_patt

logger = logging.getLogger("__name__")
router = Router()
router.message.filter(F.chat.type.in_({'private'}))


@router.message(Command(commands="course", ignore_case=True))
async def course_cmd(message: types.Message, state: FSMContext, session: AsyncSession):
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        first_name = message.chat.first_name
        now = datetime.now()
        try:
            result = await session.execute(select(Calendar).order_by(desc(Calendar.end_time)).limit(1))
            close_date = result.scalar_one()
            await session.commit()
        except NoResultFound:
            close_date = None
        if close_date is not None:
            if close_date.end_time is not None or now < close_date.end_time:
                await message.answer(f"Привет {first_name}!\nЯ собираю email адреса для платных курсов Нейропанк академии\n"
                                     f"Для начала напиши мне свой email, чтобы я предоставил тебе доступ к стриму")
                await state.set_state(Mail.start)
            else:
                await message.answer(f"Привет {first_name}!\nСейчас не время присылать email, попробуй позже")
        else:
            await message.answer(f"Привет {first_name}!\nСейчас не время присылать email, попробуй позже")


@router.message(Mail.start)
async def course_cmd(message: types.Message, state: FSMContext, session: AsyncSession):
    email = message.text
    first_name = message.from_user.first_name
    if check(email, email_patt):
        await state.update_data(email=str(message.text))
        try:
            existing_email = await session.run_sync(lambda: session.query(StreamEmails).filter(StreamEmails.email == email).one())
            await message.reply(f"{first_name}, этот Email уже был добавлен ранее!")
        except NoResultFound:
            new_email = StreamEmails(email=str(message.text), stream_id=1)
            async with session.begin():
                session.add(new_email)
                await session.commit()
            await message.reply(f"{first_name}, записал твой Email! Спасибо!\n"
                                f"Перед началом стрима на почту придет ссылка на трансляцию")
        await state.clear()
    else:
        await message.reply(f"{first_name}, это не похоже на Email попробуй снова")
