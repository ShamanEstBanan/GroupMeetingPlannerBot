import datetime
import json
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from storages import event_storage

router: Router = Router()


@router.message(Command('future_meetings'))
async def process_get_list_of_meetings(message: Message, state: FSMContext) -> None:
    chat_id = str(state.key.chat_id)
    db_events = event_storage.get_actual_events_by_chat_id(chat_id)

    # Convert to a list of JSON-compatible dictionaries
    events_list = [json.loads(json.dumps(event, default=str)) for event in db_events]
    if len(events_list) == 0:
        await message.answer(f"Извините, актуальных встреч нет.")
        return

    text = 'Актуальные встречи:'
    for event in events_list:
        date_start = datetime.datetime.fromisoformat(event['period_start'])
        date_end = datetime.datetime.fromisoformat(event['period_end'])
        text += f'\n "{event['title']}": {date_start.strftime("%d.%m.%Y")} - {date_end.strftime("%d.%m.%Y")}'
    await message.answer(text=text, reply_markup=ReplyKeyboardRemove())

    return


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
