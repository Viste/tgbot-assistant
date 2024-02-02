import logging

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from main import paper
from tools.states import Payment
from core.helpers.tools import active_chat, thread_id

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "buy_subscription")
async def get_sub(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['chatid']
    await paper.send_message(user_id,
                             "Привет!\nДля оформления подписки подтверди свое согласие - напиши да, или любое сообщение в ответ.")
    current_state = await state.get_state()
    logging.info("current state %r", current_state)
    await state.set_state(Payment.process)
    await callback.answer()


@router.callback_query()
async def process_callback(callback: types.CallbackQuery):
    global active_chat, thread_id
    if callback.data == "academy_chat":
        active_chat = -1001647523732
    elif callback.data == "np_pro":
        active_chat = -1001814931266
    elif callback.data == "np_basic":
        active_chat = -1001922960346
        thread_id = 25503
    await callback.answer_callback_query(callback.id)
