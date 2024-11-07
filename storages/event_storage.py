import logging
from dataclasses import asdict
from datetime import datetime
from typing import Mapping, Any
import isodate

from pymongo import MongoClient
from pymongo.synchronous.cursor import Cursor
from bson import ObjectId

from entities.event import Event, TimePeriod
from config_data.config import MONGO_ADDRESS

client = MongoClient(MONGO_ADDRESS)  # Adjust the URI if needed
db = client["MeetingsBot"]  # Create (or access) the database
events_collection = db["Events"]  # Create (or access) the collection


def add_new_event(e: Event) -> None:
    event = Event(
        title=e.title,
        chat_id=e.chat_id,
        author_id=e.author_id,
        period_start=e.period_start,
        period_end=e.period_end,
        chosen_day=e.chosen_day,

    )

    event_dict = asdict(event)
    event_id = events_collection.insert_one(event_dict).inserted_id
    logging.info(f'Inserted event {event_id}')
    return


def get_actual_events_by_chat_id(chat_id: str) -> Cursor[Mapping[str, Any] | Any]:
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    iso_today = isodate.parse_datetime(today)
    query = {
        "chat_id": chat_id,
        "chosen_day": {"$gt": iso_today}
    }

    events_db = events_collection.find(query)
    return events_db


def add_timeperiod_to_event(period: TimePeriod) -> None:

    query = {"_id": ObjectId(period.event_id)}

    period_dict =  asdict(period)
    update = {"$push": {"periods": period_dict}}

    result = events_collection.update_one(query, update)
    if result.modified_count > 0:
        print("Элемент успешно добавлен в periods")
    else:
        print("Запись не найдена или обновление не требовалось")
    return
