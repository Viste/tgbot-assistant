import logging

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from main import paper
from tools.states import Payment

logger = logging.getLogger("__name__")
router = Router()


@router.callback_query(F.data == "buy_subscription")
async def get_sub(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['chatid']
    await paper.send_message(user_id, "Привет! я помогу тебе приобрести подписку")
    current_state = await state.get_state()
    logging.info("current state %r", current_state)
    await state.set_state(Payment.process)
    await callback.answer()
