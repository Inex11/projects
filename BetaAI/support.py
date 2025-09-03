# A support bot

from database import Database
import os
import dotenv
from openai import OpenAI
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

class Remove(StatesGroup):
    delete = State()

class Cancel(StatesGroup):
    chat_id = State()
    message_id = State()

async def check_text(message: Message):
    text = (message.text or '').strip()
        
    if not text:
        await message.answer('Please send text')
        return None

    return text

async def propose(message: Message, state: FSMContext):
        # Buttons
        markup = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text='Add a question', callback_data='add')],
            [types.InlineKeyboardButton(text='Remove a question', callback_data='remove')],
            [types.InlineKeyboardButton(text='Answer to the client', callback_data='answer')]
        ])

        await message.answer(
            'What would you like to do?',
            reply_markup=markup
        )

async def delete_buttons(bot: Bot, chat_id: int, message_id: int):
    try:
        await bot.edit_message_reply_markup(
            chat_id=chat_id, 
            message_id=message_id, 
            reply_markup=None
        )
    except Exception as e:
        print('Problem when deleting buttons')

async def load_data(message: Message, state: FSMContext):
    data = await state.get_data()
    old_message = data['message_id']
    if old_message:
        await delete_buttons(message.bot, message.chat.id, old_message)

    return await check_text(message)

CANCEL_MARKUP = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text='Cancel', callback_data='cancel')]
])

db = Database(
    os.getenv('USER'),
    os.getenv('DB_PASSWORD'),
    os.getenv('DSN')
)

client = OpenAI(api_key=os.getenv('OPENAI_API'))



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
        
        await message.answer(f'Hello, {message.from_user.first_name}.')
        await propose(message, state)
        
    # Add command processing
    @dp.message(Command('add'))
    async def add_command(message: Message, state: FSMContext):
        ans = await message.answer(
            'Enter the question.',
            reply_markup=CANCEL_MARKUP
        )
        await state.update_data(message_id=ans.message_id)
        await state.set_state(Add.question)

    # Add button processing
    @dp.callback_query(F.data == 'add')
    async def add_first_step(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        ans = await callback.message.answer(
            'Enter the question.',
            reply_markup=CANCEL_MARKUP
        )
        await state.update_data(message_id=ans.message_id)
        await state.set_state(Add.question)

    @dp.message(Add.question)
    async def add_question(message: Message, state: FSMContext  ):
        text = await load_data(message, state)

        if text is None:
            return
        if len(text) > 150:
            ans = await message.answer(
                'The size of this question is more than 150 symbols. '
                'Write it shorter.',
                reply_markup=CANCEL_MARKUP
            )
            await state.update_data(message_id=ans.message_id)
            return
        
        await state.update_data(question=text)
        ans = await message.answer(
            "Good. Now enter the answer.",
            reply_markup=CANCEL_MARKUP
        )
        await state.update_data(message_id=ans.message_id)
        await state.set_state(Add.answer)

    @dp.message(Add.answer)
    async def add_answer(message: Message, state: FSMContext):

        text = await load_data(message, state)

        if text is None:
            return
        if len(text) > 500:
            ans = await message.answer(
                'The size of this answer is more than 500 symbols. '
                'Write it shorter.',
                reply_markup=CANCEL_MARKUP
            )
            await state.update_data(message_id=ans.message_id)
            return
        
        try:
            data = await state.get_data()
            resp = client.embeddings.create(
                input=data['question'],
                model='text-embedding-3-large'
            )
            embedding = resp.data[0].embedding  
            db.add_question(
                data['question'],
                text,
                embedding
            )
        except Exception as e:
            await message.answer('Sorry, something went wrong. :(')
            print(f'Database exception: {e}')
        else:
            await message.answer('The question was added.')
        finally:
            await state.clear()

    # Cancel button procesing
    @dp.callback_query(F.data == 'cancel')
    async def cancel(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer('You canceled the action.')
        await state.clear()

    @dp.callback_query(F.data == 'remove')
    async def remove(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        ans = await callback.message.answer(
            'Enter the id of the question to delete it from the database. '
            'Also you can enter the part of the question to get its id.',
            reply_markup=CANCEL_MARKUP
        )
        await state.update_data(message_id=ans.message_id)
        await state.set_state(Remove.delete)

    @dp.message(Remove.delete)
    async def remove_question(message: Message, state: FSMContext):
        text = await load_data(message, state)

        if not text:
            ans = await message.answer('Send the text.', reply_markup=CANCEL_MARKUP)
            await state.update_data(message_id=ans.message_id)
        else:
            try:
                num = int(text)
                db.delete_question(num)
                await message.answer('If this question was existed, it was deleted.')
            except ValueError:
                await message.answer(f'This is your text: {text}')
            finally:
                await state.clear()



    @dp.message()
    async def other_messages(message: Message, state: FSMContext):
        await propose(message, state)

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(support())