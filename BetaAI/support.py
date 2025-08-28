# A support bot

from database import Database
import os
import dotenv
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

dotenv.load_dotenv()


class Check(StatesGroup):
    password = State()

class Add(StatesGroup):
    question = State()
    answer = State()

async def check_text(message: Message):
    text = (message.text or '').strip()
        
    if not text:
        await message.answer('Please send text')
        return None

    return text

db = Database(
    os.getenv('USER'),
    os.getenv('DB_PASSWORD'),
    os.getenv('DSN')
)

# General function for support bot
async def support():
    bot = Bot(os.getenv('SUPPORT_API'))
    dp = Dispatcher()

    @dp.message(Command('start'))
    async def start(message: Message, state: FSMContext):
        await message.answer('Enter the password, please.')
        await state.set_state(Check.password)

    @dp.message(Check.password)
    async def check_password(message: Message, state: FSMContext):
        password = (message.text or '').strip()

        if password != os.getenv('PASSWORD'):
            await message.answer('The password is wrong. Try again.')
            return
        
        # Buttons
        markup = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text='Add a question', callback_data='add')],
            [types.InlineKeyboardButton(text='Remove a question', callback_data='remove')],
            [types.InlineKeyboardButton(text='Answer to the client', callback_data='answer')]
        ])

        await message.answer(
            f'Hello, {message.from_user.first_name}. '
            'Would you like to do?',
            reply_markup=markup
        )

        await state.clear()
        
    # Add command processing
    @dp.message(Command('add'))
    async def add_command(message: Message, state: FSMContext):
        await message.answer('Enter the question.')
        await state.set_state(Add.question)

    # Add button processing
    @dp.callback_query(F.data == 'add')
    async def add_first_step(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        await callback.message.answer('Enter the question.')
        await state.set_state(Add.question)

    @dp.message(Add.question)
    async def add_question(message: Message, state: FSMContext):
        text = await check_text(message)

        if text is None:
            return
        if len(text) > 150:
            await message.answer(
            'The size of this question is more than 150 symbols. '
            'Write it shorter.'
            )
            return
        
        await state.update_data(question=text)
        await message.answer("Good. Now enter the answer.")
        await state.set_state(Add.answer)

    @dp.message(Add.answer)
    async def add_answer(message: Message, state: FSMContext):
        text = await check_text(message)

        if text is None:
            return
        if len(text) > 500:
            await message.answer(
            'The size of this answer is more than 500 symbols. '
            'Write it shorter.'
            )
            return
        
        try:
            data = await state.get_data()
            db.add_question(
                data['question'],
                text,
                [1, 3, 5]
            )
        except Exception as e:
            await message.answer('Sorry, something went wrong. :(')
            print(f'Database exception: {e}')
        else:
            await message.answer('The question was added.')
        finally:
            await state.clear()

    @dp.message()
    async def message(message: Message):
        await message.answer('Please, send a command.')

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(support())