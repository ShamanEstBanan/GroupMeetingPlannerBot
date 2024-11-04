import logging
from dataclasses import asdict
from typing import Mapping, Any

import pymongo
from pymongo import MongoClient
from pymongo.synchronous.cursor import Cursor

from entities.event import Event
from config_data.config import MONGO_ADDRESS

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
    events_db = events_collection.find({"chat_id": chat_id})
    return events_db
