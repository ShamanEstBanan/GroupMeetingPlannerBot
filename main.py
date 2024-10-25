# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from itertools import combinations

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

from datetime import datetime, timedelta

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






# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    from itertools import combinations

    # Пример временных отрезков
    time_segments = [
        (0, 5),
        (3, 7),
        (6, 10),
        (8, 12),
        (2, 4),
        (5, 9),
        (1, 3),
        (10, 15)
    ]

    # Поиск лучшего пересечения для 8 временных отрезков
    max_intersecting_segments, best_interval, best_segments = find_best_intersection(time_segments)
    print('max_intersecting_segments: ', max_intersecting_segments)
    print('best_interval: ', best_interval)
    print('best_segments: ', best_segments)

    # # Пример использования
    # example_date = "25.10.2024 16:40"
    # seconds_from_nearest_monday(example_date)




