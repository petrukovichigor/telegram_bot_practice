from aiogram import Router
from aiogram.filters import Command
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from services.user_profiles import get_user_fio, set_user_fio


router = Router()


class ProfileStates(StatesGroup):
    waiting_fio = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    fio = get_user_fio(user_id)
    if fio:
        await state.clear()
        await message.answer(
            f"Здравствуйте, {fio}! 👋\n\n"
            "Чтобы начать бронирование, нажмите /book.\n"
            "Если нужна помощь по форматам времени и дат, нажмите /help."
        )
        return

    await state.clear()
    await message.answer(
        "Здравствуйте! Перед началом напишите, пожалуйста, своё **ФИО** (например: Иванов Иван Иванович).",
        parse_mode="Markdown",
    )
    await state.set_state(ProfileStates.waiting_fio)


@router.message(Command("profile"))
async def cmd_profile(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Напишите своё **ФИО**, я сохраню его и буду использовать в календаре.",
        parse_mode="Markdown",
    )
    await state.set_state(ProfileStates.waiting_fio)


@router.message(ProfileStates.waiting_fio)
async def process_fio(message: Message, state: FSMContext):
    fio = (message.text or "").strip()
    if len(fio) < 5 or fio.count(" ") < 1:
        await message.answer("Похоже, это не ФИО. Введите в формате: Фамилия Имя Отчество.")
        return

    set_user_fio(message.from_user.id, fio)
    await state.clear()
    await message.answer(
        f"Запомнил: **{fio}**.\n\nТеперь можно начинать бронировать: /book",
        parse_mode="Markdown",
    )

