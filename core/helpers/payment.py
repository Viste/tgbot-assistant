import logging
from datetime import datetime, timedelta

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from main import paper
from tools.states import Payment
from tools.utils import config

logger = logging.getLogger(__name__)
router = Router()

price = [LabeledPrice(label='demo_room', amount=35000)]


@router.message(Payment.process, F.content_type.in_({'text'}), F.chat.type == "private")
async def pay_sub(message: types.Message, state: FSMContext):
    userid = message.from_user.id
    current_state = await state.get_state()
    logging.info("Current state: %r ", current_state)
    await paper.send_invoice(userid, title='Приобретение подписки на сервис "Кибер Папер"',
                             description='Приобрести Подписку',
                             provider_token=config.payment_token, currency='RUB',
                             photo_url='https://i.pinimg.com/originals/73/a1/ec/73a1ecc7f59840a47537c012bc23d685.png',
                             photo_height=512, photo_width=512, photo_size=512, is_flexible=False, need_name=True,
                             prices=price, start_parameter='create_invoice_subscribe', payload='payload:subscribe')


@router.message(F.successful_payment)
async def got_payment_ru(message: types.Message, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    logging.info("Current state: %r ", current_state)

    logging.info('Info about message %s', message)
    now = datetime.utcnow()
    userid = message.from_user.id
    user = await session.get(User, userid)

    if user is None:
        # Create a new user and add it to the database
        user = User(
            telegram_id=message.from_user.id,
            telegram_username=message.from_user.username,
            balance_amount=350,
            max_tokens=0,
            current_tokens=0,
            subscription_start=now,
            subscription_end=now + timedelta(days=30),
            subscription_status='active',
            updated_at=now
        )
        session.add(user)
        await session.commit()
    else:
        user.subscription_start = now
        user.subscription_end = now + timedelta(days=30)
        user.subscription_status = 'active'
        user.telegram_id = message.from_user.id
        user.telegram_username = message.from_user.username
        user.balance_amount = 350

    await session.commit()
    await message.reply("Успех! Подписка оформлена")

    if current_state is None:
        return
    logging.info("Cancelling state %r", current_state)
    await state.clear()


@router.pre_checkout_query(lambda query: True)
async def process_pay_sub(pre_checkout_query: types.PreCheckoutQuery, state: FSMContext):
    data = await state.get_data()
    current_state = await state.get_state()

    if current_state is None:
        return
    elif "Payment" in current_state:
        await paper.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        await paper.send_message(chat_id=config.info_channel,
                                 text=f"Пришла оплата за донат, ID платежа: {pre_checkout_query.id}\n"
                                      f"Telegram user: {pre_checkout_query.from_user.first_name}\n"
                                      f"Кто: {pre_checkout_query.order_info.name}")

        logging.info("Current state %r, chat_id = %s", current_state, data)
        await state.set_state(Payment.process)
