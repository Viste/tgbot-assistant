import logging

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from fluent.runtime import FluentLocalization

from core.helpers.tools import ChatState
from core.helpers.tools import chat_settings
from main import paper
from tools.states import Payment, CoursePayment

# from sqlalchemy.ext.asyncio import AsyncSession
# from database.manager import UserManager

router = Router()
logger = logging.getLogger(__name__)
chat_state = ChatState()


@router.callback_query(F.data == "buy_subscription")
async def get_sub(callback: types.CallbackQuery, state: FSMContext, l10n: FluentLocalization):
    data = await state.get_data()
    logging.info("current state data %s", data)
    user_id = data['chatid']
    await paper.send_message(user_id, l10n.format_value("sub-agreement"))
    await state.set_state(Payment.process)
    current_state = await state.get_state()
    logging.info("current state %r", current_state)
    await callback.answer()


@router.callback_query(F.data == "buy_course")
async def get_course(callback: types.CallbackQuery, state: FSMContext, l10n: FluentLocalization):
    await callback.message.reply(l10n.format_value("ask-sub-mail"))
    await state.set_state(CoursePayment.start)
    await callback.answer()


@router.callback_query(lambda c: c.data in chat_settings)
async def process_sender(callback: types.CallbackQuery):
    logger.info("Callback query received: %s", callback.data)
    settings = chat_settings[callback.data]
    chat_state.active_chat = settings["active_chat"]
    if "thread_id" in settings:
        chat_state.thread_id = settings["thread_id"]
    logging.info('State changed: active_chat=%s, thread_id=%s', chat_state.active_chat, chat_state.thread_id)
    await callback.answer()


# @router.callback_query(lambda c: c.data.startswith("course_"))
# async def process_catcher(callback: types.CallbackQuery, session: AsyncSession):
    # logger.info("Callback query received: %s", callback.data)
    # course_name = None
    # manager = UserManager(session)

    # if callback.data.startswith("course_"):
    #     if callback.data == "course_np_pro":
    #         course_name = "НЕЙРОПАНК PRO (КОНТЕНТ ПО ПОДПИСКЕ) by Paperclip"

    # if course_name:
    # emails = await manager.get_emails_by_course(course_name=course_name)
    # if emails:
    #    email_list = "\n".join(emails)
    #    await callback.message.answer(f"Email адреса участников курса '{course_name}':\n{email_list}")
    # else:
    #    await callback.message.answer(f"Участников на курсе '{course_name}' не найдено.")
    # else:
    #    await callback.answer("Неизвестный курс.", show_alert=True)
