import json
import logging
import uuid
from datetime import datetime, timedelta

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from fluent.runtime import FluentLocalization
from sqlalchemy.ext.asyncio import AsyncSession

from core.helpers.tools import Robokassa
from core.helpers.tools import generate_robokassa_link, get_payment_status_message, private_filter
from database.manager import UserManager
from database.models import User, NeuropunkPro
from tools.states import Payment, CoursePayment
from tools.utils import config, check_payment, Merchant, Order

router = Router()
logger = logging.getLogger(__name__)

merchant = Merchant(config.rb_login, config.rb_pass1, config.rb_pass2)
robokassa_payment = Robokassa(merchant)
now = datetime.utcnow()


@router.message(Payment.process, F.content_type.in_({'text'}), private_filter)
async def pay_sub_process(message: types.Message, state: FSMContext, l10n: FluentLocalization):
    random_id = uuid.uuid4().int & (1 << 24) - 1
    order = Order(random_id, 'подписка на сервис киберпапер', 500.0)
    link = await robokassa_payment.generate_payment_link(order)
    check_link = await generate_robokassa_link(config.rb_login, random_id, config.rb_pass2)
    await state.update_data(check_link=check_link)
    logging.info("Current robokassa link: %s ", link)

    kb = [
        [types.InlineKeyboardButton(text=l10n.format_value("pay-default-sub"), url=link)],
        ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer(l10n.format_value("check-pay-answer"), reply_markup=keyboard)
    await state.set_state(Payment.end)


@router.message(Payment.end, F.text.regexp(r"[\s\S]+?оплатил[\s\S]+?") | F.text.startswith("оплатил"), private_filter)
async def pay_sub_end(message: types.Message, state: FSMContext, session: AsyncSession, l10n: FluentLocalization):
    data = await state.get_data()
    check_link = data['check_link']
    user_manager = UserManager(session)
    logging.info("Current robokassa check link from private sub end %s", check_link)
    result_str = await check_payment(check_link)
    logging.info("Payment result from sub end %s", result_str)
    userid = message.from_user.id
    user = await user_manager.get_user(userid)
    try:
        result = json.loads(result_str)
    except json.JSONDecodeError:
        await message.answer(l10n.format_value("unknown-payment-error"))
        return

    status_message = get_payment_status_message(result, l10n)
    if status_message == 0:
        if user is None:
            user = User(telegram_id=message.from_user.id, telegram_username=message.from_user.username, balance_amount=500, max_tokens=0, current_tokens=0, subscription_start=now,
                        subscription_end=now + timedelta(days=30), subscription_status='active', updated_at=now)
            await user_manager.create_user(user)
            await message.answer(status_message)
        else:
            user.subscription_start = now
            user.subscription_end = now + timedelta(days=30)
            user.subscription_status = 'active'
            user.telegram_id = message.from_user.id
            user.telegram_username = message.from_user.username
            user.balance_amount = 500
            await session.commit()
            await message.answer(status_message)
    else:
        await message.answer(status_message)


@router.message(CoursePayment.start, F.content_type.in_({'text'}), F.text.regexp(r"^[a-zA-Z0-9._%+-]+?@gmail\.com"))
async def pay_course(message: types.Message, state: FSMContext, l10n: FluentLocalization):
    random_id = uuid.uuid4().int & (1 << 24) - 1
    email = message.text
    order = Order(random_id, 'подписка на сервис киберпапер', 1500.0)
    link = await robokassa_payment.generate_payment_link(order)
    check_link = await generate_robokassa_link(config.rb_login, random_id, config.rb_pass2)
    await state.update_data(check_link=check_link)
    await state.update_data(email=email)
    logging.info("Current robokassa link: %s ", link)
    logging.info("Current user email: %s ", email)
    kb = [
        [types.InlineKeyboardButton(text=l10n.format_value("pay-course-sub"), url=link)],
        ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.reply(l10n.format_value("check-pay-answer"), reply_markup=keyboard)
    await state.set_state(CoursePayment.end)


@router.message(CoursePayment.end, F.text.regexp(r"[\s\S]+?оплатил[\s\S]+?") | F.text.startswith("оплатил"))
async def pay_course_end(message: types.Message, state: FSMContext, session: AsyncSession, l10n: FluentLocalization):
    data = await state.get_data()
    user_id = message.from_user.id
    user_manager = UserManager(session)
    user = await user_manager.get_course_user(user_id)
    check_link = data['check_link']
    email = data['email']
    result_str = await check_payment(check_link)

    logging.info("Current robokassa check link %s", check_link)
    logging.info("Payment result in course %s", result_str)
    try:
        result = json.loads(result_str)
    except json.JSONDecodeError:
        await message.reply(l10n.format_value("unknown-payment-error"))
        return

    status_message = get_payment_status_message(result, l10n)
    if status_message == 0:
        if user is None:
            user = NeuropunkPro(telegram_id=message.from_user.id, telegram_username=message.from_user.username, email=email, subscription_start=now,
                                subscription_end=now + timedelta(days=30),
                                subscription_status='active', updated_at=now)
            await user_manager.create_user(user)
            await message.reply(status_message)
        else:
            user.subscription_start = now
            user.subscription_end = now + timedelta(days=30)
            user.subscription_status = 'active'
            user.telegram_id = message.from_user.id
            user.telegram_username = message.from_user.username
            user.email = email
            await session.commit()
            await message.reply(status_message)
    else:
        await message.reply(status_message)
