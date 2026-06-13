import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import config

# Путь к файлу с ключами, который ты скачал
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=creds)

async def create_event(data: dict, initiator: str):
    """
    Создает событие в Google Calendar.
    data: словарь с данными из FSM (date, time, room, equipment, notes)
    initiator: имя пользователя
    """
    service = get_calendar_service()

    # Парсим дату и время для Google (ему нужен формат ISO: YYYY-MM-DDTHH:MM:SS)
    # Дата у нас в формате DD.MM.YYYY, время "HH:MM – HH:MM"
    date_parts = data['date'].split('.')
    day, month, year = date_parts[0], date_parts[1], date_parts[2]
    
    time_start, time_end = data['time'].split(' – ')
    
    start_iso = f"{year}-{month}-{day}T{time_start}:00"
    end_iso = f"{year}-{month}-{day}T{time_end}:00"

    equipment = (data.get("equipment") or "").strip()
    equipment_is_empty = equipment in {"", "-", "не требуется"}

    # Формируем тело события согласно ТЗ (п. 3.4)
    event_body = {
        'summary': (
            f"Бронирование аудитории {data['room']}"
            if equipment_is_empty
            else f"Бронирование {equipment} в {data['room']}"
        ),  # C-06
        'location': data['room'], # C-04
        'description': f"Инициатор: {initiator}\nЗаявка подана: {datetime.datetime.now().strftime('%d.%m %H:%M')}\nПримечания: {data['notes']}", # C-05
        'start': {
            'dateTime': start_iso,
            'timeZone': 'Europe/Moscow',
        },
        'end': {
            'dateTime': end_iso,
            'timeZone': 'Europe/Moscow',
        },
    }
    # НОВОЕ: Добавляем логику повторов (RRULE)
    if data.get('repeat_type') == "WEEKLY":
        count = data.get('repeat_count', 1)
        # RRULE:FREQ=WEEKLY;COUNT=5 означает "каждую неделю, всего 5 раз"
        event_body['recurrence'] = [f'RRULE:FREQ=WEEKLY;COUNT={count}']

    # Отправляем запрос в Google
    event = service.events().insert(calendarId=config.CALENDAR_ID, body=event_body).execute()
    
    # Возвращаем ссылку на событие (C-07)
    return event.get('htmlLink')