from dataclasses import dataclass
from enum import Enum

class EventStatus(Enum):
    CREATED = 'CREATED'
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELED = "canceled"



@dataclass
class Event:
    chat_id: str
    title: str
    week_start: str
    week_end: str
    author_id: str
    status: EventStatus
    day:str