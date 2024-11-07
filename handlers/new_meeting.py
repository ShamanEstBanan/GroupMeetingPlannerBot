import json
import logging
from datetime import datetime
from typing import List

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

import helpers.time_calculator
from entities.event import Event
from storages import event_storage

router: Router = Router()


class Meeting(StatesGroup):
    title = State()
    period_start = State()
    period_end = State()


@router.message(Command('new_meeting'))
async def process_create_new_meeting(message: Message, state: FSMContext) -> None:
    await state.set_state(Meeting.title)
    await message.answer(
        "Введине название встречи:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Meeting.title)
async def process_meeting_title(message: Message, state: FSMContext) -> None:
    title = message.text
    await state.update_data(title=title)
    await state.set_state(Meeting.period_start)
    await message.answer(
        "Давайте выберем диапазон дней в который произойдет встреча\n" +
        "Введите первый день диапазона, например 12.04.1961:",
        reply_markup=ReplyKeyboardMarkup(keyboard =[[]] ),
    )


@router.message(Meeting.period_start)
async def process_period_start(message: Message, state: FSMContext) -> None:
    period_start = message.text
    await state.update_data(period_start=period_start)
    await state.set_state(Meeting.period_end)
    await message.answer(
        "Введите последний день, например 20.04.1961:",
    )


@router.message(Meeting.period_end)
async def process_period_end(message: Message, state: FSMContext) -> None:
    period_end = message.text
    await state.update_data(period_end=period_end)

    current_data = await state.get_data()
    period_start = current_data.get('period_start')
    period_end = current_data.get('period_end')

    chat_id = str(state.key.chat_id)
    author_id = str(state.key.user_id)

    new_event = Event(
        title=current_data.get('title'),
        period_start=datetime.strptime(period_start, "%d.%m.%Y"),
        period_end=datetime.strptime(period_end, "%d.%m.%Y"),
        author_id=author_id,
        chat_id=chat_id,
        chosen_day=datetime.today(),
    )

    event_storage.add_new_event(new_event)
    await message.answer(
        f'Отлично, встреча произойдет на неделе {period_start}-{period_end}! Осталось выбрать лучшее время!',
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()
