import logging

from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from fluent.runtime import FluentLocalization

from tools.states import Payment, NpPayment, ZoomPayment

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "buy_subscription")
async def get_sub(callback: types.CallbackQuery, state: FSMContext, l10n: FluentLocalization, bot: Bot) -> None:
    data = await state.get_data()
    logger.info("current state data %s", data)
    user_id = data['chatid']
    await bot.send_message(user_id, l10n.format_value("sub-agreement"))
    await state.set_state(Payment.process)
    current_state = await state.get_state()
    logger.info("current state %r", current_state)
    await callback.answer()


@router.callback_query(F.data == "buy_nppro")
async def get_course_np_pro(callback: types.CallbackQuery, state: FSMContext, l10n: FluentLocalization):
    await state.set_state(NpPayment.start)
    current_state = await state.get_state()
    logger.info("FROM CoursePayment.start state %r", current_state)
    await callback.message.reply(l10n.format_value("ask-sub-email"))
    await callback.answer()


@router.callback_query(F.data == "buy_zoom")
async def get_course_zoom(callback: types.CallbackQuery, state: FSMContext, l10n: FluentLocalization):
    await state.set_state(ZoomPayment.start)
    current_state = await state.get_state()
    logger.info("FROM CoursePayment.start state %r", current_state)
    await callback.message.reply(l10n.format_value("ask-sub-email"))
    await callback.answer()
