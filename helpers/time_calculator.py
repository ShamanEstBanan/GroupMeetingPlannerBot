from datetime import datetime, timedelta
from itertools import combinations


def find_best_intersection(time_segments):
    """
    Находит максимальное количество временных отрезков, имеющих общее пересечение, и сам интервал пересечения.
    Возвращает максимальное число отрезков с пересечением и соответствующий интервал.
    """
    max_intersecting_segments = 0
    best_interval = None
    best_segments = []

    # Итерируем от большего количества отрезков к меньшему
    for r in range(len(time_segments), 0, -1):
        for subset in combinations(time_segments, r):
            # Найти общий интервал для текущего подмножества
            max_start = max(t_start for t_start, _ in subset)
            min_end = min(t_end for _, t_end in subset)

            # Проверяем, есть ли пересечение
            if max_start <= min_end:
                # Обновляем, если нашли большее количество отрезков с пересечением
                if r > max_intersecting_segments:
                    max_intersecting_segments = r
                    best_interval = (max_start, min_end)
                    best_segments = subset

    return max_intersecting_segments, best_interval, best_segments


def seconds_from_nearest_monday(date_str):
    """
    Преобразует дату и время в формате 'dd.mm.yyyy hh:mm' в количество секунд от начала ближайшего понедельника.
    """
    # Преобразуем строку в datetime
    date_time = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
    print(date_time)
    # Находим ближайший понедельник, предшествующий или равный дате
    days_since_monday = (date_time.weekday() + 1) % 7  # 0 = Monday, ..., 6 = Sunday
    print(days_since_monday)
    nearest_monday = date_time - timedelta(days=days_since_monday,
                                           hours=date_time.hour,
                                           minutes=date_time.minute)
    print(nearest_monday)

    # Вычисляем разницу во времени от ближайшего понедельника до данной даты
    seconds_difference = int((date_time - nearest_monday).total_seconds())

    print(seconds_difference)
    return seconds_difference


def get_nearest_monday_sunday(given_date):
    # Смещение до понедельника и воскресенья
    days_to_monday = (given_date.weekday() - 0) % 7
    days_to_sunday = (6 - given_date.weekday()) % 7

    # Вычисляем ближайшие даты понедельника и воскресенья
    monday_date = given_date - timedelta(days=days_to_monday)
    sunday_date = given_date + timedelta(days=days_to_sunday)

    return {"Monday": monday_date, "Sunday": sunday_date}

def calculate_week_by_data(date: str) -> dict:
    date = datetime.strptime(f"{date}.{datetime.now().year}", "%d.%m.%Y")

    week = get_nearest_monday_sunday(date)

    return {"Monday": week['Monday'].strftime("%d.%m.%Y"), "Sunday": week['Sunday'].strftime("%d.%m.%Y")}