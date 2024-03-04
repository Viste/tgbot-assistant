import logging
import uuid
import json

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from database.manager import UserManager as user_manager
from database.models import User
from tools.utils import config
from tools.states import Payment
from tools.scheme import Merchant, Order
from core.helpers.robokassa import Robokassa, check_payment
from core.helpers.tools import generate_robokassa_link, get_payment_status_message, private_filter

router = Router()
logger = logging.getLogger(__name__)

merchant = Merchant(config.rb_login, config.rb_pass1, config.rb_pass2)
robokassa_payment = Robokassa(merchant)


@router.message(Payment.process, F.content_type.in_({'text'}), private_filter)
async def pay_sub_process(message: types.Message, state: FSMContext):
    random_id = uuid.uuid4().int & (1 << 24) - 1
    order = Order(random_id, 'подписка на сервис киберпапер', 500.0)
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


@router.message(Payment.end, F.text.regexp(r"[\s\S]+?оплатил[\s\S]+?") | F.text.startswith("оплатил"), private_filter)
async def pay_sub_end(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    check_link = data['check_link']
    logging.info("Current robokassa check link %s", check_link)
    result_str = await check_payment(check_link)
    logging.info("RESULT OF PAYMENT %s", result_str)
    now = datetime.utcnow()
    userid = message.from_user.id
    user = await user_manager(session).get_user(userid)
    try:
        result = json.loads(result_str)
    except json.JSONDecodeError:
        await message.answer("Произошла ошибка при обработке ответа от сервиса. Пожалуйста, попробуйте позже или обратитесь в поддержку.")
        return

    status_message = get_payment_status_message(result)
    if status_message == 0:
        if user is None:
            user = User(telegram_id=message.from_user.id, telegram_username=message.from_user.username, balance_amount=500, max_tokens=0, current_tokens=0, subscription_start=now,
                        subscription_end=now + timedelta(days=30), subscription_status='active', updated_at=now)
            await user_manager(session).create_user(user)
            await message.answer(status_message)
        else:
            user.subscription_start = now
            user.subscription_end = now + timedelta(days=30)
            user.subscription_status = 'active'
            user.telegram_id = message.from_user.id
            user.telegram_username = message.from_user.username
            user.balance_amount = 350
            await session.commit()
            await message.answer(status_message)
    else:
        await message.answer(status_message)
