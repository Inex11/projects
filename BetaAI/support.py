# A support bot

import os
import dotenv
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State


class Check(StatesGroup):
    password = State()

dotenv.load_dotenv()

async def support():
    bot = Bot(os.getenv('SUPPORT_API'))
    dp = Dispatcher()

    @dp.message(Command('start'))
    async def start(message: Message, state: FSMContext):
        await message.answer('Enter the password, please.')
        await state.set_state(Check.password)

    @dp.message(Check.password)
    async def check_password(message: Message, state: FSMContext):
        password = message.text.strip()

        if password != os.getenv('PASSWORD'):
            await message.answer('The password is wrong. Try again.')
            return
        
        markup = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text='Add a question', callback_data='add')],
            [types.InlineKeyboardButton(text='Remove a question', callback_data='remove')],
            [types.InlineKeyboardButton(text='Answer to the client', callback_data='answer')]     
        ])

        await message.answer(
            f"Hello, {message.from_user.first_name}. "
            "Would you like to change something "
            "or just answer some questions?",
            reply_markup=markup
        )

        await state.clear()

    @dp.message()
    async def message(message: Message):
        await message.answer('Please, send a command.')

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(support())