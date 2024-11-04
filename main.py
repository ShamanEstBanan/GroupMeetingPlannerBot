import asyncio
import copy
import json
import logging
import sys
import typing

from dataclasses import asdict,dataclass
from typing import Any, List, Mapping

from aiogram import Bot, Dispatcher, html, types, Router, F
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from pymongo import MongoClient
from pymongo.synchronous.cursor import Cursor
import helpers.time_calculator
from config import API_TOKEN
from enum import Enum
from config_data.config import MONGO_ADDRESS


class EventStatus(Enum):
    CREATED = 'CREATED'
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELED = "canceled"

class Meeting(StatesGroup):
    new = State()
    title = State()
    weekday = State()


@dataclass
class Event:
    chat_id: str
    title: str
    week_start: str
    week_end: str
    author_id: str
    status: EventStatus
    day:str


events = []
meetings_router = Router()

client = MongoClient(MONGO_ADDRESS)  # Adjust the URI if needed
db = client["MeetingsBot"]  # Create (or access) the database
events_collection = db["Events"]  # Create (or access) the collection


def insert_event(e: Event) -> None:
    event = Event(
        chat_id=e.chat_id,
        title=e.title,
        week_start=e.week_start,
        week_end=e.week_end,
        author_id=e.author_id,
        status=e.status,
        day=e.day,

    )

    event_dict = asdict(event)
    event_dict['status'] = event.status.value
    event_id = events_collection.insert_one(event_dict).inserted_id
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


dp = Dispatcher()


@dp.message(CommandStart())
async def send_welcome(message: types.Message) -> None:
    await message.reply("Привет! Я помогу вам выбрать лучшее время для встречи!\n"
                        "Команда /help поможет узнать доступные команды")


@dp.message(Command('help'))
async def send_welcome(message: types.Message) -> None:
    await message.reply("Команды:\n"
                        "/start Начало работы бота\n"
                        "/help Узнать справочную информацию\n"
                        "/meetings Посмотреть список встреч или создать новую")


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
    chat_id = str(state.key.chat_id)
    await show_actual_meetings(message=message, actual_meetings=events, chat_id=chat_id)


async def show_actual_meetings(message: Message, actual_meetings: List, chat_id: str) -> None:
    db_events = get_events_by_chat_id(chat_id)
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


@meetings_router.message(Meeting.new, F.text.casefold() == "создать новую встречу")
async def process_create_new_meeting(message: Message, state: FSMContext) -> None:
    await state.set_state(Meeting.title)
    await message.answer(
        "Введине название встречи:",
        reply_markup=ReplyKeyboardRemove(),
    )

@meetings_router.message(Meeting.new, F.text.casefold() == "нет")
async def process_decline_creating_meeting(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Хорошо!",
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
        week_start=start_and_finish['Monday'],
        week_end=start_and_finish['Sunday'],
        author_id=author_id,
        chat_id=chat_id,
        status=EventStatus.CREATED,
        day='',
    )

    events.append(new_event)
    insert_event(new_event)
    await message.answer(
        f'Отлично, встреча произойдет на неделе {new_event.week_start}-{new_event.week_end}! Осталось выбрать лучшее время!',
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
