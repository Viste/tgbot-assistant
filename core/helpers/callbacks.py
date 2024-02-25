import logging

from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import CourseParticipant

from main import paper
from tools.states import Payment
from core.helpers.tools import ChatState
from database.manager import UserManager

router = Router()
logger = logging.getLogger(__name__)
state = ChatState()


@router.callback_query(F.data == "buy_subscription")
async def get_sub(callback: types.CallbackQuery, pay_state: FSMContext):
    data = await pay_state.get_data()
    user_id = data['chatid']
    await paper.send_message(user_id,
                             "Привет!\nДля оформления подписки подтверди свое согласие - напиши да, или любое сообщение в ответ.")
    current_state = await pay_state.get_state()
    logging.info("current state %r", current_state)
    await pay_state.set_state(Payment.process)
    await callback.answer()


@router.callback_query()
async def process_sender(callback: types.CallbackQuery):
    logger.info("Callback query received: %s", callback.data)
    if callback.data == "academy_chat":
        state.active_chat = -1001647523732
        logging.info('state changed to academy %s', state.active_chat)
    elif callback.data == "np_pro":
        state.active_chat = -1001814931266
        state.thread_id = 12
        logging.info('state changed to pro %s', state.active_chat)
    elif callback.data == "np_basic":
        state.active_chat = -1001922960346
        state.thread_id = 25503
        logging.info('state changed to basic %s', state.active_chat)
    elif callback.data == "liquid_chat":
        state.active_chat = -1001999768206
        state.thread_id = 4284
        logging.info('state changed to liquid %s', state.active_chat)
    elif callback.data == "super_pro":
        state.active_chat = -1002040950538
        state.thread_id = 293
        logging.info('state changed to SUPER PRO %s', state.active_chat)
    elif callback.data == "neuro":
        state.active_chat = -1001961684542
        state.thread_id = 4048
        logging.info('state changed to NEURO %s', state.active_chat)
    await callback.answer()


@router.callback_query(F.data.startswith("course_"))
async def process_catcher(callback: types.CallbackQuery, session: AsyncSession, bot: Bot, catch_state: FSMContext):
    logger.info("Callback query received: %s", callback.data)
    manager = UserManager(session)
    data = await catch_state.get_data()
    user_id = data['chatid']
    if callback.data == "course_academy":
        course_name = "Нейропанк Академия (Общий поток)"
        stmt = select(CourseParticipant.email).where(CourseParticipant.course_name == course_name)
        logger.info("Course name: %s", course_name)
        result = await session.execute(stmt)
        emails = result.scalars().all()
        logging.info(f"Retrieved emails for course {course_name}: {emails}")
        if emails:
            logger.info("Emails: %s", emails)
            email_list = "\n".join(emails)
            logger.info("Emails: %s", email_list)
            await bot.send_message(chat_id=user_id, text=f"Email адреса участников курса '{course_name}':\n{email_list}")
            await callback.answer()
        else:
            await bot.send_message(chat_id=user_id, text=f"Участников на курсе '{course_name}' не найдено.")
            await callback.answer()
    elif callback.data == "course_np_pro":
        course_name = "Нейропанк Академия (Общий поток)"
        emails = await manager.get_emails_by_course(course_name=course_name)
        if emails:
            email_list = "\n".join(emails)
            await callback.message.answer(f"Email адреса участников курса '{course_name}':\n{email_list}")
        else:
            await callback.message.answer(f"Участников на курсе '{course_name}' не найдено.")
    elif callback.data == "course_np_basic":
        course_name = "НАЧАЛЬНЫЙ #1 - от 0 до паладина!"
        emails = await manager.get_emails_by_course(course_name=course_name)
        if emails:
            email_list = "\n".join(emails)
            await callback.message.answer(f"Email адреса участников курса '{course_name}':\n{email_list}")
        else:
            await callback.message.answer(f"Участников на курсе '{course_name}' не найдено.")
    elif callback.data == "course_liquid":
        course_name = "ЛИКВИД КУРС #1 - Нейропанк Академия"
        emails = await manager.get_emails_by_course(course_name=course_name)
        if emails:
            email_list = "\n".join(emails)
            await callback.message.answer(f"Email адреса участников курса '{course_name}':\n{email_list}")
        else:
            await callback.message.answer(f"Участников на курсе '{course_name}' не найдено.")
    elif callback.data == "course_super_pro":
        course_name = "SUPER PRO#1 (DNB)"
        emails = await manager.get_emails_by_course(course_name=course_name)
        if emails:
            email_list = "\n".join(emails)
            await callback.message.answer(f"Email адреса участников курса '{course_name}':\n{email_list}")
        else:
            await callback.message.answer(f"Участников на курсе '{course_name}' не найдено.")
    elif callback.data == "course_neuro":
        course_name = "НЕЙРОФАНК КУРС #1"
        emails = await manager.get_emails_by_course(course_name=course_name)
        if emails:
            email_list = "\n".join(emails)
            await callback.message.answer(f"Email адреса участников курса '{course_name}':\n{email_list}")
        else:
            await callback.message.answer(f"Участников на курсе '{course_name}' не найдено.")
