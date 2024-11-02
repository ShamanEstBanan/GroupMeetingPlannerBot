import asyncio
import copy
import json
import logging
import sys
import typing

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, List, Mapping

from aiogram import Bot, Dispatcher, html, types, Router, F
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, )
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import pymongo
from pymongo import MongoClient
from pymongo.synchronous.cursor import Cursor

import helpers.time_calculator
from config import API_TOKEN


class Meeting(StatesGroup):
    new = State()
    title = State()
    weekday = State()


@dataclass
class Event:
    chat_id: str
    title: str
    start: str
    end: str
    author_id: str


events = []
meetings_router = Router()

client = MongoClient("mongodb://localhost:27017/")  # Adjust the URI if needed
db = client["MeetingsBot"]  # Create (or access) the database
events_collection = db["Events"]  # Create (or access) the collection


def insert_event(e: Event) -> None:
    event = {
        'chat_id': e.chat_id,
        'title': e.title,
        'start': e.start,
        'end': e.end,
        'author_id': e.author_id,
    }

    event_id = events_collection.insert_one(event).inserted_id
    logging.info(f'Inserted event {event_id}')
    return


def get_events_by_chat_id(chat_id: str) -> Cursor[Mapping[str, Any] | Any]:
    logging.info(f'chatId for serching:...{chat_id}')
    events_db = events_collection.find({"chat_id": chat_id})
    return events_db


# @meetings_router.message(Command("cancel"))
# @meetings_router.message(F.text.casefold() == "cancel")
# async def cancel_handler(message: Message, state: FSMContext) -> None:
#     """
#     Allow user to cancel any action
#     """
#     current_state = await state.get_state()
#     if current_state is None:
#         return
#
#     logging.info("Cancelling state %r", current_state)
#     await state.clear()
#     await message.answer(
#         "Cancelled.",
#         reply_markup=ReplyKeyboardRemove(),
#     )
#
#
# def keyboard_meetings():
#     builder = InlineKeyboardBuilder()
#
#     builder.button(text='Создать новую встречу', )
#     builder.button(text='Посмотреть список актуальных встреч')
#     builder.adjust(2, 2)
#
#     return builder.as_markup(resize_keyboard=True, input_field_placeholder="test")
#

dp = Dispatcher()


@dp.message(CommandStart())
async def send_welcome(message: types.Message) -> None:
    await message.reply("Привет! Я помогу вам выбрать лучшее время для встречи!")


@meetings_router.message(Command('meetings'))
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


@meetings_router.message(Meeting.new, F.text.casefold() == "посмотреть список")
async def process_get_list_of_meetings(message: Message, state: FSMContext) -> None:
    await state.clear()
    chat_id = str(state.key.chat_id)
    await show_actual_meetings(message=message, actual_meetings=events, chat_id=chat_id)


async def show_actual_meetings(message: Message, actual_meetings: List, chat_id: str) -> None:
    db_events = get_events_by_chat_id(chat_id)
    # Convert to a list of JSON-compatible dictionaries
    events_list = [json.loads(json.dumps(event, default=str)) for event in db_events]
    if len(events_list) == 0:
        await message.answer(text="Извините, нет актуальных встреч", reply_markup=ReplyKeyboardRemove())
        return

    # db_events = get_events_by_chat_id(chat_id)
    logging.info(f'What we have in DB:\n{events_list}')

    text = 'Предстоящие встречи:'
    for event in events_list:
        text += f'\n "{event['title']}": {event['start']}-{event['end']}'
    await message.answer(text=text, reply_markup=ReplyKeyboardRemove())
    return


@meetings_router.message(Meeting.new, F.text.casefold() == "создать новую встречу")
async def process_create_new_meeting(message: Message, state: FSMContext) -> None:
    await state.set_state(Meeting.title)
    await message.answer(
        "Введине название встречи:",
        reply_markup=ReplyKeyboardRemove(),
    )


@meetings_router.message(Meeting.title)
async def process_meeting_title(message: Message, state: FSMContext) -> None:
    title = message.text
    await state.update_data(title=title)
    await state.set_state(Meeting.weekday)
    await message.answer(
        "Нужно определиться на какой неделе провести встречу." +
        "Введите любую дату в формате '31.12' на желаемой неделе:",
    )


@meetings_router.message(Meeting.weekday)
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
        start=start_and_finish['Monday'],
        end=start_and_finish['Sunday'],
        author_id=author_id,
        chat_id=chat_id,
    )

    events.append(new_event)
    insert_event(new_event)
    await message.answer(
        f'Отлично, встреча произойдет на неделе {new_event.start}-{new_event.end}! Осталось выбрать лучшее время!',
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp.include_router(meetings_router)

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('start to make bot')

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
