import logging

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from main import paper
from tools.states import Payment
from core.helpers.tools import ChatState
from core.helpers.tools import chat_settings
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


@router.callback_query(lambda c: c.data in chat_settings)
async def process_sender(callback: types.CallbackQuery):
    logger.info("Callback query received: %s", callback.data)
    settings = chat_settings[callback.data]
    state.active_chat = settings["active_chat"]
    if "thread_id" in settings:
        state.thread_id = settings["thread_id"]
    logging.info('State changed: active_chat=%s, thread_id=%s', state.active_chat, state.thread_id)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("course_"))
async def process_catcher(callback: types.CallbackQuery, session: AsyncSession):
    logger.info("Callback query received: %s", callback.data)
    course_name = None
    manager = UserManager(session)

    if callback.data.startswith("course_"):
        if callback.data == "course_academy":
            course_name = "Нейропанк Академия (Общий поток)"
        elif callback.data == "course_np_pro":
            course_name = "НЕЙРОПАНК PRO (КОНТЕНТ ПО ПОДПИСКЕ) by Paperclip"
        elif callback.data == "course_np_basic":
            course_name = "НАЧАЛЬНЫЙ #1 - от 0 до паладина!"
        elif callback.data == "course_liquid":
            course_name = "ЛИКВИД КУРС #1 - Нейропанк Академия"
        elif callback.data == "course_super_pro":
            course_name = "SUPER PRO#1 (DNB)"
        elif callback.data == "course_neuro":
            course_name = "НЕЙРОФАНК КУРС #1"
        elif callback.data == "course_nerve":
            course_name = "NERV3 Продуктивность Level 99 #1"
        elif callback.data == "course_girls":
            course_name = "DNB Курс - только девушки! 🤖🤖🤖"

        if course_name:
            emails = await manager.get_emails_by_course(course_name=course_name)
            if emails:
                email_list = "\n".join(emails)
                await callback.message.answer(f"Email адреса участников курса '{course_name}':\n{email_list}")
            else:
                await callback.message.answer(f"Участников на курсе '{course_name}' не найдено.")
        else:
            await callback.answer("Неизвестный курс.", show_alert=True)
