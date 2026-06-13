import dateparser
import re
from datetime import datetime, timedelta

# Настройки парсера дат для русского языка
DATEPARSER_SETTINGS = {
    'PREFER_DATES_FROM': 'future', # Искать даты в будущем
    'DATE_ORDER': 'DMY',           # Формат День-Месяц-Год
    'RETURN_AS_TIMEZONE_AWARE': False
}

def parse_user_date(text: str):
    """Превращает 'завтра', '26 марта', 'в пятницу' в объект datetime"""
    parsed_date = dateparser.parse(text, languages=['ru'], settings=DATEPARSER_SETTINGS)
    return parsed_date

def parse_user_time(text: str):
    """
    Извлекает интервал времени.
    Поддерживает форматы: '8:15-11:15', 'с 8 до 11', 'на 2 пары с 9:00'
    """
    text = text.lower().replace(" ", "")
    
    # 1. Поиск стандартного интервала HH:MM-HH:MM или H:MM-H:MM
    pattern_full = r'(\d{1,2}:\d{2})-(\d{1,2}:\d{2})'
    match_full = re.search(pattern_full, text)
    if match_full:
        return match_full.group(1), match_full.group(2)

    # 2. Поиск интервала 'с 8 до 11'
    pattern_simple = r'(?:с|от)(\d{1,2})(?:до|по)(\d{1,2})'
    match_simple = re.search(pattern_simple, text)
    if match_simple:
        start = f"{match_simple.group(1)}:00"
        end = f"{match_simple.group(2)}:00"
        return start, end

    # 3. Логика 'пар' из ТЗ (1 пара = 1 час 25 минут)
    # Например: 'на 2 пары с 8:15', 'на 1 пару с 8:15', 'на 1 пара с 8:15'
    pattern_pairs = r'на(\d+)пар(?:а|ы|у)?с(\d{1,2}:\d{2})'
    match_pairs = re.search(pattern_pairs, text)
    if match_pairs:
        count = int(match_pairs.group(1))
        start_str = match_pairs.group(2)
        
        start_dt = datetime.strptime(start_str, "%H:%M")
        # 1 пара = 85 мин, перемена между парами = 10 мин
        duration = count * 85 + max(0, count - 1) * 10
        end_dt = start_dt + timedelta(minutes=duration)
        
        return start_str, end_dt.strftime("%H:%M")

    return None, None