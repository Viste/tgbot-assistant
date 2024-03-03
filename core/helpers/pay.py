import logging
import uuid

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from tools.utils import config
from tools.states import Payment
from core.helpers.model.scheme import Merchant, Order
from core.helpers.robokassa import Robokassa, check_payment
from core.helpers.tools import generate_robokassa_link

router = Router()
logger = logging.getLogger(__name__)

merchant = Merchant(config.rb_login, config.rb_pass1, config.rb_pass2)
robokassa_payment = Robokassa(merchant)


@router.message(Payment.process, F.content_type.in_({'text'}), F.chat.type == "private")
async def pay_sub(message: types.Message, state: FSMContext):
    random_id = uuid.uuid4().int & (1 << 24) - 1
    order = Order(random_id, 'подписка на сервис киберпапер', 100.0)
    link = await robokassa_payment.generate_payment_link(order)
    check_link = await generate_robokassa_link(config.rb_login, random_id, config.rb_pass2)
    await state.update_data(check_link=check_link)
    logging.info("Current robokassa link: %s ", link)

    kb = [
        [types.InlineKeyboardButton(text="Оплатить 500 рублей за подписку", url=link)],
        ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer("Для оплаты нажми на кнопку ниже. А после оплаты напиши 'оплатил', а я проверю ;)", reply_markup=keyboard)
    await state.set_state(Payment.end)


@router.message(Payment.end, F.text.regexp(r"[\s\S]+?оплатил[\s\S]+?") | F.text.startswith("оплатил"), F.chat.type == "private")
async def pay_sub(message: types.Message, state: FSMContext):
    data = await state.get_data()
    check_link = data['check_link']
    logging.info("Current robokassa check link %s", check_link)
    result = await check_payment(check_link)
    logging.info("RESULT OF PAYMENT %s", result)
