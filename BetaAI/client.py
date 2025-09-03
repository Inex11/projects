import random
import os
import asyncio
import dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import openai

dotenv.load_dotenv()

async def client():
    bot = Bot(os.getenv('CLIENT_API'))
    dp = Dispatcher()

    openai.api_key = os.getenv('OPENAI_API')

    try:
        f = open('prompt.txt', 'r')
    except FileNotFoundError:
        print('The prompt.txt file was not found.')
        return

    chats = [{'role': 'system', 'content': f.read()}]

    @dp.message(Command('start'))
    async def start(message: Message, state: FSMContext):
        answers = (
            'Welcome to Beta Bank’s virtual assistant. How may I assist you today?',
            'Hello, you’ve reached the Beta Bank AI Assistant. What can I help you with?',
            'Good day, this is Beta Bank’s digital support. How may I be of service?    ',
            'Thank you for contacting Beta Bank. I’m your AI assistant—how can I assist?',
            'Greetings from Beta Bank. I’m here to help with your banking questions.'
        )

        await message.answer(random.choice(answers))

    @dp.message(F.text)
    async def chat(message: Message):
        try:
            chats.append({'role': 'user', 'content': message.text})

            response = openai.chat.completions.create(
                model='gpt-5',
                messages=chats,
                max_completion_tokens=500
            )

            answer = response.choices[0].message.content
            chats.append({'role': 'assistant', 'content': answer})
            await message.answer(answer)
            
        except Exception as e:
            await message.answer('Sorry, there are some problems with OpenAI api.')
            print(f'Problems with OpenAI API: {e}')
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(client())