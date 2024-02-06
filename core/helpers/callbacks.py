import logging

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from main import paper
from tools.states import Payment
from core.helpers.tools import ChatState

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
async def process_callback(callback: types.CallbackQuery):
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
    elif callback.data == "liqud_chat":
        state.active_chat = -1001999768206
        state.thread_id = 4284
        logging.info('state changed to liquid %s', state.active_chat)
    await callback.answer()
