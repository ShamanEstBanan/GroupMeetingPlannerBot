import json
import logging
from typing import List

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

import helpers.time_calculator
from entities.event import Event, EventStatus
from storages import event_storage

router: Router = Router()


class Meeting(StatesGroup):
    new = State()
    title = State()
    weekday = State()


@router.message(Command('meetings'))
async def meetings_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(Meeting.new)
    await message.answer(
        f"Вы хотите создать новую встречу или посмотреть список актуальных?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="создать новую встречу"),
                    KeyboardButton(text="посмотреть список"),
                ]
            ],
            resize_keyboard=True,
        ),
    )


@router.message(Meeting.new, F.text.casefold() == "посмотреть список")
async def process_get_list_of_meetings(message: Message, state: FSMContext) -> None:
    chat_id = str(state.key.chat_id)
    await show_actual_meetings(message=message, chat_id=chat_id)


async def show_actual_meetings(message: Message, chat_id: str) -> None:
    db_events = event_storage.get_events_by_chat_id(chat_id)

    # Convert to a list of JSON-compatible dictionaries
    events_list = [json.loads(json.dumps(event, default=str)) for event in db_events]
    if len(events_list) == 0:
        await message.answer(
            f"Извините, намеченный встреч нет. Хотите создать новую?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text="создать новую встречу"),
                        KeyboardButton(text="нет"),
                    ]
                ],
                resize_keyboard=True,
            ),
        )
        return

    # db_events = get_events_by_chat_id(chat_id)
    logging.info(f'What we have in DB:\n{events_list}')

    text = 'Предстоящие встречи:'
    for event in events_list:
        text += f'\n "{event['title']}": {event['week_start']}-{event['week_end']}'
    await message.answer(text=text, reply_markup=ReplyKeyboardRemove())

    await message.answer(
        f"Хотите создать новую встречу?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="создать новую встречу"),
                    KeyboardButton(text="нет"),
                ]
            ],
            resize_keyboard=True,
        ),
    )
    return


@router.message(Meeting.new, F.text.casefold() == "создать новую встречу")
async def process_create_new_meeting(message: Message, state: FSMContext) -> None:
    await state.set_state(Meeting.title)
    await message.answer(
        "Введине название встречи:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Meeting.new, F.text.casefold() == "нет")
async def process_decline_creating_meeting(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Хорошо!",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Meeting.title)
async def process_meeting_title(message: Message, state: FSMContext) -> None:
    title = message.text
    await state.update_data(title=title)
    await state.set_state(Meeting.weekday)
    await message.answer(
        "Нужно определиться на какой неделе провести встречу." +
        "Введите любую дату в формате '31.12' на желаемой неделе:",
    )


@router.message(Meeting.weekday)
async def process_meeting_weekday(message: Message, state: FSMContext) -> None:
    weekday = message.text
    await state.update_data(weekday=weekday)

    current_data = await state.get_data()
    weekday = current_data.get('weekday')
    start_and_finish = helpers.time_calculator.calculate_week_by_data(weekday)

    chat_id = str(state.key.chat_id)
    author_id = str(state.key.user_id)

    new_event = Event(
        title=current_data.get('title'),
        week_start=start_and_finish['Monday'],
        week_end=start_and_finish['Sunday'],
        author_id=author_id,
        chat_id=chat_id,
        status=EventStatus.CREATED,
        day='',
    )

    event_storage.insert_event(new_event)
    await message.answer(
        f'Отлично, встреча произойдет на неделе {new_event.week_start}-{new_event.week_end}! Осталось выбрать лучшее время!',
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()


@router.message(Command("cancel"))
@router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )


