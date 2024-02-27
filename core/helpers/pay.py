import logging
from datetime import datetime, timedelta

from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice
from sqlalchemy.ext.asyncio import AsyncSession

from database.manager import UserManager as manager
from database.models import User
from tools.states import Payment
from tools.utils import config

router = Router()
logger = logging.getLogger(__name__)


@router.message(Payment.process, F.content_type.in_({'text'}), F.chat.type == "private")
async def pay_sub(message: types.Message, state: FSMContext, bot: Bot):
    userid = message.from_user.id
    current_state = await state.get_state()
    logging.info("Current state: %r ", current_state)
    # тут надо оплатку замутить #
