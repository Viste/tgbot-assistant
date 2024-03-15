import logging

from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from fluent.runtime import FluentLocalization
from sqlalchemy.ext.asyncio import AsyncSession

from core.helpers.tools import ChatState
from core.helpers.tools import chat_settings
from database.manager import Manager
from database.models import NeuropunkPro, Zoom
from tools.states import Payment, NpPayment, ZoomPayment

router = Router()
logger = logging.getLogger(__name__)
chat_state = ChatState()


@router.callback_query(F.data == "buy_subscription")
async def get_sub(callback: types.CallbackQuery, state: FSMContext, l10n: FluentLocalization, bot: Bot) -> None:
    data = await state.get_data()
    logger.info("current state data %s", data)
    user_id = data['chatid']
    await bot.send_message(user_id, l10n.format_value("sub-agreement"))
    await state.set_state(Payment.process)
    current_state = await state.get_state()
    logger.info("current state %r", current_state)
    await callback.answer()


@router.callback_query(F.data == "buy_nppro")
async def get_course_np_pro(callback: types.CallbackQuery, state: FSMContext, l10n: FluentLocalization):
    await state.set_state(NpPayment.start)
    current_state = await state.get_state()
    logger.info("FROM CoursePayment.start state %r", current_state)
    await callback.message.reply(l10n.format_value("ask-sub-email"))
    await callback.answer()


@router.callback_query(F.data == "buy_zoom")
async def get_course_zoom(callback: types.CallbackQuery, state: FSMContext, l10n: FluentLocalization):
    await state.set_state(ZoomPayment.start)
    current_state = await state.get_state()
    logger.info("FROM CoursePayment.start state %r", current_state)
    await callback.message.reply(l10n.format_value("ask-sub-email"))
    await callback.answer()


@router.callback_query(lambda c: c.data in chat_settings)
async def process_sender(callback: types.CallbackQuery):
    logger.info("Callback query received: %s", callback.data)
    settings = chat_settings[callback.data]
    chat_state.active_chat = settings["active_chat"]
    if "thread_id" in settings:
        chat_state.thread_id = settings["thread_id"]
    logger.info('State changed: active_chat=%s, thread_id=%s', chat_state.active_chat, chat_state.thread_id)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("course_"))
async def process_catcher(callback: types.CallbackQuery, session: AsyncSession):
    user_manager = Manager(session)

    course_models = {
        "course_np_pro": NeuropunkPro,
        "course_zoom": Zoom,
    }
    for key, model in course_models.items():
        if callback.data.startswith(key):
            emails = await user_manager.get_active_emails(model)

            if emails:
                emails_str = ', '.join(emails)
                await callback.message.answer(f"Активные email адреса подписчиков курса: {emails_str}")
            else:
                await callback.message.answer("Нет активных подписчиков курса с указанными email адресами.")
            break
