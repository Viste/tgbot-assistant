import logging

from aiogram import types, Router
from aiogram.fsm.context import FSMContext

from main import paper
from tools.states import Payment
from tools.utils import config

logger = logging.getLogger("__name__")
router = Router()


@router.pre_checkout_query(lambda query: True)
async def process_pay_sub(pre_checkout_query: types.PreCheckoutQuery, state: FSMContext):
    data = await state.get_data()
    current_state = await state.get_state()

    if current_state is None:
        return
    elif "Payment" in current_state:
        await paper.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        await paper.send_message(chat_id=config.info_channel, text=f"Пришла оплата за донат, ID платежа: {pre_checkout_query.id}\n"
                                                                   f"Telegram user: {pre_checkout_query.from_user.first_name}\n"
                                                                   f"Кто: {pre_checkout_query.order_info.name}")

        logging.info("Current state %r, chat_id = %s", current_state, data)
        await state.set_state(Payment.get)
