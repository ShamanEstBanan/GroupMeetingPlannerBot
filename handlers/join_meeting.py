import datetime
import json
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup

from entities.event import TimePeriod
from storages import event_storage

router: Router = Router()


class Meeting(StatesGroup):
    idx = State()
    period_day = State()
    timeperiod_start = State()
    timeperiod_end = State()


buttons_indexes = []
future_events = []


@router.message(Command('join_meeting'))
async def process_get_list_of_meetings(message: Message, state: FSMContext) -> None:
    chat_id = str(state.key.chat_id)
    user_name = str(message.from_user.full_name)

    print(user_name)
    await state.update_data(user_name=user_name)

    db_events = event_storage.get_actual_events_by_chat_id(chat_id)

    # Convert to a list of JSON-compatible dictionaries
    events_list = [json.loads(json.dumps(event, default=str)) for event in db_events]

    for event in events_list:
        future_events.append(event)

    if len(events_list) == 0:
        await message.answer(f"Извините, актуальных встреч нет.")
        return

    await state.set_state(Meeting.idx)
    keyboard = [[]]
    text = 'Актуальные встречи:'
    for idx, event in enumerate(events_list):
        beautiful_idx = idx + 1
        date_start = datetime.datetime.fromisoformat(event['period_start'])
        date_end = datetime.datetime.fromisoformat(event['period_end'])
        text += f'\n {beautiful_idx}. "{event['title']}": {date_start.strftime("%d.%m.%Y")} - {date_end.strftime("%d.%m.%Y")}'
        keyboard[0].append(KeyboardButton(text=f'{beautiful_idx}'))
        buttons_indexes.append(f'{beautiful_idx}')

    await message.answer(text=text, reply_markup=ReplyKeyboardRemove())
    await message.answer("Выберете встречу:",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=keyboard,
                             resize_keyboard=True,
                         )
                         )

    return


@router.message(Meeting.idx)
async def process_idx_meeting(message: Message, state: FSMContext) -> None:
    idx = int(message.text)
    await state.update_data(event_idx=idx - 1)
    await state.set_state(Meeting.period_day)

    keyboard = [[]]

    day_start = datetime.datetime.strptime(future_events[idx - 1]['period_start'], "%Y-%m-%d %H:%M:%S")
    day_end = datetime.datetime.strptime(future_events[idx - 1]['period_end'], "%Y-%m-%d %H:%M:%S")

    # Генерация списка дней
    days_in_range = []
    current_date = day_start
    while current_date <= day_end:
        days_in_range.append(current_date)
        current_date += datetime.timedelta(days=1)

    for day in days_in_range:
        keyboard[0].append(KeyboardButton(text=f'{day.strftime("%d-%m-%Y")}'))

    await message.answer(
        f"Всреча запланирована в период {day_start.strftime("%d-%m-%Y")} - {day_end.strftime("%d-%m-%Y")}")
    await message.answer(f"Нужно выбрать в какие дни этого периода и в какое время вы можете посетить встречу.")
    await message.answer("Выберете день:",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=keyboard,
                             resize_keyboard=True,
                         )
                         )

    return


@router.message(Meeting.period_day)
async def process_day_meeting(message: Message, state: FSMContext) -> None:
    day = message.text
    await state.update_data(period_day=day)
    await state.set_state(Meeting.timeperiod_start)
    await message.answer(
        "Пожалуйста, укажите ваш комфортный промежуток времени для встречи (например, с 10:00 до 18:00)\n"
        "Введите начало периода времени:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Meeting.timeperiod_start)
async def process_timeperiod_start(message: Message, state: FSMContext) -> None:
    time = message.text
    await state.update_data(start_time=time)
    await state.set_state(Meeting.timeperiod_end)
    await message.answer(
        "Введите конец периода времени:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Meeting.timeperiod_end)
async def process_timeperiod_end(message: Message, state: FSMContext) -> None:
    time = message.text
    await state.update_data(end_time=time)

    current_data = await state.get_data()
    start_time = current_data.get('start_time')
    end_time = current_data.get('end_time')
    period_day = current_data.get('period_day')
    user_name = current_data.get('user_name')

    idx = current_data.get('event_idx')
    event_id = future_events[idx - 1]['_id']


    d = current_data.get('period_day')
    period_day = datetime.datetime.strptime(d, "%d-%m-%Y")

    await message.answer(
        f'Вы добавили  период времени {start_time} - {end_time}, {period_day} ',
        reply_markup=ReplyKeyboardRemove(),
    )
    chat_id = str(state.key.chat_id)
    user_id = str(state.key.user_id)

    new_period = TimePeriod(
        user_name = user_name,
        user_id=user_id,
        event_id=event_id,
        chat_id=chat_id,
        day=period_day,
        start_time=datetime.datetime.strptime(start_time, "%H:%M"),
        end_time=datetime.datetime.strptime(end_time, "%H:%M")
    )

    event_storage.add_timeperiod_to_event(new_period)
    await message.answer(
        "Вы можете добавить еще один промежуток времени для текущего дня, выбрать другой день или закончить",
        reply_markup=ReplyKeyboardRemove(), )


@router.message(Meeting.period_day)
async def process_period_day(message: Message, state: FSMContext) -> None:
    period_day = int(message.text)
    await state.update_data(period_day=period_day)


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
