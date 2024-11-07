from dataclasses import dataclass
from datetime import datetime


@dataclass()
class TimePeriod:
    user_name: str
    user_id: str
    event_id: str
    chat_id: str
    day: datetime
    start_time: datetime
    end_time: datetime


@dataclass
class Event:
    """
    title: title of the event
    author_id: author of the event
    chat_id: chat_id where the event is located
    period_start: first day of days range for choosing the best day
    period_end:  last day of days range for choosing the best day
    chosen_day:  final day of event
    status: EventStatus
    """
    title: str
    author_id: str
    chat_id: str
    period_start: datetime
    period_end: datetime
    chosen_day: datetime
