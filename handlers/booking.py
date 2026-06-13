from aiogram import F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

from services.calendar_api import create_event
import config # Для получения ID админа

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from services.parser import parse_user_date, parse_user_time
from services.user_profiles import get_user_fio

router = Router()

def get_confirm_kb(): # Клавиатура для подтверждения бронирования
    buttons = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking")],
        [InlineKeyboardButton(text="📝 Изменить", callback_data="edit_booking")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 **Шпаргалка по использованию бота**\n\n"
        "Я помогу вам забронировать аудиторию и автоматически внесу запись в Google Календарь.\n\n"
        "✨ **Основные команды:**\n"
        "/book — Начать бронирование\n"
        "/help — Показать это сообщение\n"
        "/start — Перезапустить бота\n\n"
        "🗓 **Как вводить дату:**\n"
        "Бот понимает естественный язык: `сегодня`, `завтра`, `в эту пятницу`, `25 мая`.\n\n"
        "🕒 **Как вводить время:**\n"
        "• Интервал: `8:15-11:15` или `с 10 до 12`\n"
        "• По парам: `на 2 пары / на 1 пару с 8:15` (1 пара = 1 час 25 мин)\n\n"
        "🛠 **Процесс:**\n"
        "1. Ответьте на вопросы бота (дата, время, место, оборудование).\n"
        "2. Выберите, нужно ли повторять бронь каждую неделю.\n"
        "3. Проверьте данные в итоговой карточке и нажмите «Подтвердить».\n\n"
        "⚠️ Если вы ошиблись, на этапе подтверждения нажмите «Изменить». До этого момента данные нельзя будет изменить."
    )
    await message.answer(help_text, parse_mode="Markdown")

# Структура состояний бронирования аудиторий
class BookingStates(StatesGroup):
    waiting_date = State()
    waiting_time = State()
    waiting_room = State()
    waiting_equipment = State() 
    waiting_notes = State()
    waiting_repeat = State()
    waiting_confirm = State()

@router.message(Command("book"))
async def start_booking(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("На какую дату нужно забронировать аудиторию? (например: сегодня, завтра, 26 марта)")
    await state.set_state(BookingStates.waiting_date)

@router.message(BookingStates.waiting_date)
async def process_date(message: Message, state: FSMContext):
    parsed_date = parse_user_date(message.text)
    
    if parsed_date:
        # Сохраняем и красивую строку, и сам объект даты (пригодится для Google)
        date_str = parsed_date.strftime("%d.%m.%Y")
        await state.update_data(date=date_str)
        
        await message.answer(f"Распознал дату: {date_str}\nТеперь введите время (например, 8:15-11:15 или 'на 2 пары с 9:00'):")
        await state.set_state(BookingStates.waiting_time)
    else:
        await message.answer("Не удалось понять дату. Попробуйте еще раз (например: завтра, 25 мая, в эту субботу)")

@router.message(BookingStates.waiting_time)
async def process_time(message: Message, state: FSMContext):
    start, end = parse_user_time(message.text)
    
    if start and end:
        time_range = f"{start} – {end}"
        await state.update_data(time=time_range)
        await message.answer(f"Распознано время: {time_range}\nУкажите номер аудитории:")
        await state.set_state(BookingStates.waiting_room)
    else:
        await message.answer("Неверный формат времени. Используйте форматы:\n- 8:15-11:15\n- с 10 до 12\n- на 2 пары с 9:00")

@router.message(BookingStates.waiting_room)
async def process_room(message: Message, state: FSMContext):
    await state.update_data(room=message.text)
    # Спрашиваем ТОЛЬКО оборудование (с возможностью пропуска)
    await message.answer("Какое оборудование требуется? (проектор, ноутбук и т.д.). Если ничего не нужно, отправьте «-»")
    await state.set_state(BookingStates.waiting_equipment)

# НОВЫЙ ШАГ: обрабатываем оборудование и спрашиваем примечания
@router.message(BookingStates.waiting_equipment)
async def process_equipment(message: Message, state: FSMContext):
    equipment = message.text
    if equipment.lower() in ["нет", "-", "нету"]:
        equipment = "не требуется"
        
    await state.update_data(equipment=equipment)
    
    await message.answer("Есть ли какие-то примечания к бронированию? Если нет, просто отправьте «-»")
    await state.set_state(BookingStates.waiting_notes)

@router.message(BookingStates.waiting_notes)
async def process_notes(message: Message, state: FSMContext):
    notes = message.text if message.text not in ["нет", "-", "нету"] else "-"
    await state.update_data(notes=notes)
    
    # Создаем простые кнопки для выбора
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Один раз")],
        [KeyboardButton(text="Еженедельно")]
    ], resize_keyboard=True, one_time_keyboard=True)
    
    await message.answer("Как часто повторять мероприятие?", reply_markup=kb)
    await state.set_state(BookingStates.waiting_repeat)

# 2. Обрабатываем выбор повтора
@router.message(BookingStates.waiting_repeat)
async def process_repeat(message: Message, state: FSMContext):
    if message.text == "Еженедельно":
        await message.answer(
            "Сколько недель подряд проводить бронирование, учитывая эту неделю? (введите число, например: 5)",
            reply_markup=ReplyKeyboardRemove(),
        )
        # Мы остаемся в этом же состоянии, но запомним, что ждем число
        await state.update_data(repeat_type="WEEKLY")
        return # Ждем следующего сообщения с числом
    
    # Если ввели число (когда уже выбрали WEEKLY)
    if message.text.isdigit():
        count = int(message.text)
        await state.update_data(repeat_count=count)
        await show_summary(message, state) # Переходим к итогу
    
    # Если выбрали "Один раз"
    elif message.text == "Один раз":
        await state.update_data(repeat_type="NONE", repeat_count=1)
        await show_summary(message, state)
    else:
        await message.answer("Пожалуйста, выберите вариант на кнопках или введите количество недель числом.")

# 3. Вынесем показ итога в отдельную функцию, чтобы не дублировать код
async def show_summary(message: Message, state: FSMContext):
    user_data = await state.get_data()
    repeat_text = "нет" if user_data.get('repeat_type') == "NONE" else f"каждую неделю, {user_data.get('repeat_count')} раз"
    
    # Формируем идеальную карточку из п. 3.3
    summary_text = (
        f"📅 Дата: {user_data['date']}\n"
        f"⏰ Время: {user_data['time']}\n"
        f"📍 Место: {user_data['room']}\n"
        f"💻 Оборудование: {user_data['equipment']}\n"
        f"📝 Примечания: {user_data['notes']}\n"
        f"🔄 Повтор: {repeat_text}\n\n"
        f"Всё верно? (Да / Отмена / Изменить)"
    )

    await message.answer("Показываю итог бронирования.", reply_markup=ReplyKeyboardRemove())
    await message.answer(summary_text, reply_markup=get_confirm_kb())
    await state.set_state(BookingStates.waiting_confirm)

    # 1. Если пользователь нажал "Подтвердить"
@router.callback_query(F.data == "confirm_booking", BookingStates.waiting_confirm)
async def cmd_confirm(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    initiator = get_user_fio(callback.from_user.id) or (callback.from_user.username or callback.from_user.full_name)

    await callback.message.edit_text("⏳ Секунду, создаю событие в календаре...")

    try:
        # ВЫЗЫВАЕМ НАШ СЕРВИС КАЛЕНДАРЯ
        event_link = await create_event(user_data, initiator)

        await callback.message.edit_text(
            f"✅ Готово! Аудитория забронирована.\n",
           parse_mode="Markdown"
        )

        # Уведомляем админа (п. 3.5 ТЗ)
        admin_ids = config.ADMIN_IDS.split(',')  # Если в .env ID через запятую
        for admin_id in admin_ids:
            admin_id = admin_id.strip()  # Очищаем от случайных пробелов
            if not admin_id:
                continue

            try:
                # ИСПРАВЛЕНО: Текст объединен в одну строку
                await callback.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 *Новое бронирование!*\n*{initiator}* забронировал(а) аудиторию *{user_data['room']}* на *{user_data['date']}*\n🔗 [Ссылка на событие]({event_link})",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Не удалось отправить админу {admin_id}: {e}")

        await state.clear()

    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при создании события: {e}")

# 2. Если пользователь нажал "Отмена"
@router.callback_query(F.data == "cancel_booking", BookingStates.waiting_confirm)
async def cmd_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Бронирование отменено. Чтобы начать заново, введите /book")

# 3. Если пользователь нажал "Изменить"
@router.callback_query(F.data == "edit_booking", BookingStates.waiting_confirm)
async def cmd_edit(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Давайте начнем сначала. На какую дату нужна аудитория?")
    await state.set_state(BookingStates.waiting_date)