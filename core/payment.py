import logging
import uuid
from datetime import datetime, timedelta

from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.methods import CreateChatInviteLink
from fluent.runtime import FluentLocalization
from sqlalchemy.ext.asyncio import AsyncSession

from core.helpers.tools import Robokassa, send_payment_message, update_or_create_user
from core.helpers.tools import generate_robokassa_link, get_payment_status_message, reg_course
from database.models import NeuropunkPro, User, Zoom
from filters.filters import PrivateFilter
from tools.data import Merchant, Order
from tools.dependencies import container
from tools.states import Payment, NpPayment, ZoomPayment
from tools.utils import check_payment, gmail_patt, check, zoom_chat, np_pro_chat

router = Router()
logger = logging.getLogger(__name__)
config = container.get('config')
merchant = Merchant(config.rb_login, config.rb_pass1, config.rb_pass2)
robokassa_payment = Robokassa(merchant)


@router.message(Payment.process, F.content_type.in_({'text'}), PrivateFilter())
async def pay_sub_process(message: types.Message, state: FSMContext, l10n: FluentLocalization):
    random_id = uuid.uuid4().int & (1 << 24) - 1
    order = Order(random_id, 'подписка на сервис киберпапер', 500.0)
    link = await robokassa_payment.generate_payment_link(order)
    check_link = await generate_robokassa_link(config.rb_login, random_id, config.rb_pass2)
    await state.update_data(check_link=check_link)
    logger.info("Current robokassa link: %s ", link)
    await send_payment_message(message, link, l10n, "pay-default-sub", "check-pay-answer")
    await state.set_state(Payment.end)


@router.message(Payment.end, (F.text.regexp(r"[\s\S]+?оплатил[\s\S]+?") | F.text.startswith("оплатил")), PrivateFilter())
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
            'used_tokens': 0, 'subscription_start': now, 'subscription_end': now + timedelta(days=30),
            'subscription_status': 'active'}
        await message.reply(status_message)
        await update_or_create_user(session, user_data, User)
    else:
        await message.reply(status_message)


@router.message(NpPayment.start, F.content_type.in_({'text'}), PrivateFilter())
async def pay_course(message: types.Message, state: FSMContext, l10n: FluentLocalization):
    random_id = uuid.uuid4().int & (1 << 24) - 1
    email = message.text
    if check(email, gmail_patt):
        order = Order(random_id, 'Месячная подписка на Нейропанк Про.', 1500.0)
        link = await robokassa_payment.generate_payment_link(order)
        check_link = await generate_robokassa_link(config.rb_login, random_id, config.rb_pass2)
        await state.update_data(check_link=check_link, email=email)
        logger.info("Current robokassa link: %s ", link)
        await send_payment_message(message, link, l10n, "pay-np-pro-sub", "check-pay-answer")
        await state.set_state(NpPayment.end)
    else:
        await message.reply(f"{message.from_user.first_name}, это не похоже на Email попробуй снова")


@router.message(NpPayment.end,
                (F.text.regexp(r"^(о|О)платил") | F.text.startswith("оплатил") | F.text.startswith("Оплатил")),
                PrivateFilter())
async def pay_course_end(message: types.Message, state: FSMContext, session: AsyncSession, l10n: FluentLocalization, bot: Bot):
    data = await state.get_data()
    now = datetime.utcnow()
    check_link = data['check_link']
    email = data['email']
    logger.info("Current robokassa check link %s", check_link)
    result = await check_payment(check_link)
    logger.info("Payment result in course %s", result)
    result_code = int(result.get("Result", {}).get("Code", "-1"))
    status_message = get_payment_status_message(result_code, l10n)
    link = await bot(CreateChatInviteLink(chat_id=np_pro_chat, member_limit=1))

    if result_code == 0:
        user_data = {
            'telegram_id': message.from_user.id, 'telegram_username': message.from_user.username,
            'email': email, 'subscription_start': now, 'subscription_end': now + timedelta(days=30),
            'subscription_status': 'active'}
        await message.answer(text=f"Для входа в чат курса перейди по ссылке: {link.invite_link}")
        await message.reply(status_message)
        await update_or_create_user(session, user_data, NeuropunkPro)
        await reg_course(message, session, "np_pro_sub")
    else:
        await message.reply(status_message)


@router.message(ZoomPayment.start, F.content_type.in_({'text'}), PrivateFilter())
async def pay_course(message: types.Message, state: FSMContext, l10n: FluentLocalization):
    random_id = uuid.uuid4().int & (1 << 24) - 1
    email = message.text
    if check(email, gmail_patt):
        order = Order(random_id, 'Альбом: Приморский EP + плагины', 20000.0)
        link = await robokassa_payment.generate_payment_link(order)
        check_link = await generate_robokassa_link(config.rb_login, random_id, config.rb_pass2)
        await state.update_data(check_link=check_link, email=email)
        logger.info("Current robokassa link: %s ", link)
        await send_payment_message(message, link, l10n, "pay-zoom-sub", "check-pay-answer")
        await state.set_state(ZoomPayment.end)
    else:
        await message.reply(f"{message.from_user.first_name}, это не похоже на Email попробуй снова")


@router.message(ZoomPayment.end,
                (F.text.regexp(r"^(о|О)платил") | F.text.startswith("оплатил") | F.text.startswith("Оплатил")),
                PrivateFilter())
async def pay_course_end(message: types.Message, state: FSMContext, session: AsyncSession, l10n: FluentLocalization, bot: Bot):
    data = await state.get_data()
    check_link = data['check_link']
    email = data['email']
    logger.info("Current robokassa check link %s", check_link)
    result = await check_payment(check_link)
    logger.info("Payment result in course %s", result)
    result_code = int(result.get("Result", {}).get("Code", "-1"))
    status_message = get_payment_status_message(result_code, l10n)
    link = await bot(CreateChatInviteLink(chat_id=zoom_chat, member_limit=1))
    if result_code == 0:
        user_data = {
            'telegram_id': message.from_user.id, 'telegram_username': message.from_user.username,
            'email': email}
        # await message.reply(status_message)
        await message.answer(text=f"Для входа в чат курса перейди по ссылке: {link.invite_link}")
        await update_or_create_user(session, user_data, Zoom)
        await reg_course(message, session, "zoom")
    else:
        await message.reply(status_message)
