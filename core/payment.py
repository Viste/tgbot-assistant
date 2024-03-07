import logging
import uuid
from datetime import datetime, timedelta

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from fluent.runtime import FluentLocalization
from sqlalchemy.ext.asyncio import AsyncSession

from core.helpers.tools import Robokassa, send_payment_message, update_or_create_user
from core.helpers.tools import generate_robokassa_link, get_payment_status_message, private_filter, subscribe_chat_filter

from tools.states import Payment, CoursePayment
from tools.utils import config, check_payment, Merchant, Order, gmail_patt, check

router = Router()
logger = logging.getLogger(__name__)

merchant = Merchant(config.rb_login, config.rb_pass1, config.rb_pass2)
robokassa_payment = Robokassa(merchant)


@router.message(Payment.process, F.content_type.in_({'text'}), private_filter)
async def pay_sub_process(message: types.Message, state: FSMContext, l10n: FluentLocalization):
    random_id = uuid.uuid4().int & (1 << 24) - 1
    order = Order(random_id, 'подписка на сервис киберпапер', 500.0)
    link = await robokassa_payment.generate_payment_link(order)
    check_link = await generate_robokassa_link(config.rb_login, random_id, config.rb_pass2)
    await state.update_data(check_link=check_link)
    logger.info("Current robokassa link: %s ", link)
    await send_payment_message(message, link, l10n, "pay-default-sub", "check-pay-answer")
    await state.set_state(Payment.end)


@router.message(Payment.end, (F.text.regexp(r"[\s\S]+?оплатил[\s\S]+?") | F.text.startswith("оплатил")), private_filter)
async def pay_sub_end(message: types.Message, state: FSMContext, session: AsyncSession, l10n: FluentLocalization):
    now = datetime.utcnow()
    data = await state.get_data()
    check_link = data['check_link']
    logger.info("Current robokassa check link from private sub end %s", check_link)
    result = await check_payment(check_link)
    logger.info("Payment result from sub end %s", result)
    result_code = int(result.get("Result", {}).get("Code", "-1"))
    status_message = get_payment_status_message(result_code, l10n)

    logger.info("Payment status_message from sub end %s", status_message)
    if result_code == 0:
        user_data = {
            'telegram_id': message.from_user.id, 'telegram_username': message.from_user.username, 'balance_amount': 500,
            'max_tokens': 0, 'current_tokens': 0, 'subscription_start': now,
            'subscription_end': now + timedelta(days=30), 'subscription_status': 'active'}
        await message.reply(status_message)
        await update_or_create_user(session, user_data)
    else:
        await message.reply(status_message)


@router.message(CoursePayment.start, F.content_type.in_({'text'}), subscribe_chat_filter)
async def pay_course(message: types.Message, state: FSMContext, l10n: FluentLocalization):
    random_id = uuid.uuid4().int & (1 << 24) - 1
    email = message.text
    if check(email, gmail_patt):
        order = Order(random_id, 'Месячная подписка на курс Нейропанк Про.', 1500.0)
        link = await robokassa_payment.generate_payment_link(order)
        check_link = await generate_robokassa_link(config.rb_login, random_id, config.rb_pass2)
        await state.update_data(check_link=check_link, email=email)
        logger.info("Current robokassa link: %s ", link)
        await send_payment_message(message, link, l10n, "pay-course-sub", "check-pay-answer")
        await state.set_state(CoursePayment.end)
    else:
        await message.reply(f"{message.from_user.first_name}, это не похоже на Email попробуй снова")


@router.message(CoursePayment.end, (F.text.regexp(r"^(о|О)платил") | F.text.startswith("оплатил") | F.text.startswith("Оплатил")), subscribe_chat_filter)
async def pay_course_end(message: types.Message, state: FSMContext, session: AsyncSession, l10n: FluentLocalization):
    data = await state.get_data()
    now = datetime.utcnow()
    check_link = data['check_link']
    email = data['email']
    logger.info("Current robokassa check link %s", check_link)
    result = await check_payment(check_link)
    logger.info("Payment result in course %s", result)
    result_code = int(result.get("Result", {}).get("Code", "-1"))
    status_message = get_payment_status_message(result_code, l10n)

    if result_code == 0:
        user_data = {
            'telegram_id': message.from_user.id, 'telegram_username': message.from_user.username,
            'email': email, 'subscription_start': now, 'subscription_end': now + timedelta(days=30),
            'subscription_status': 'active'}
        await message.reply(status_message)
        await update_or_create_user(session, user_data, is_course=True)
    else:
        await message.reply(status_message)
