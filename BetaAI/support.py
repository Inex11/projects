# A support bot

import os
import dotenv
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

dotenv.load_dotenv()

async def support():
    bot = Bot(os.getenv('SUPPORT_API'))
    dp = Dispatcher()

    @dp.message(Command('start'))
    async def start(message: Message):
        await message.answer('The bot was activated.')

    @dp.message()
    async def message(message: Message):
        await message.answer(message.text)

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(support)