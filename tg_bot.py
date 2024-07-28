# -*- coding: utf-8 -*-

#
# Основной модуль
# Парсим
#


from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import CommandStart

# 
# aioschedule давно не обновлялась. Надо заменить в файле
# env\Lib\site-packages\aioschedule\__init__.py 
# строку 107
# jobs = [job.run() for job in self.jobs if job.should_run]
# на
# jobs = [asyncio.create_task(job.run()) for job in self.jobs if job.should_run]
import aioschedule as schedule

#
from config import token, kk_channel_id, bot_chat_id
from parser_regions_ru import parse_regions_ru
from inline import get_inline_keys

#
import asyncio
import logging
import sys

bot = Bot(token, parse_mode=ParseMode.HTML)
dp = Dispatcher()
last_message = ''

# Проверка токена
# @dp.message()
# async def start_answer(message):
#     await message.answer(text=message.text)

# Сохранение в память последнего сообщения пользователя
@dp.message()
async def start_answer(message):
    global last_message
    last_message = message.text


async def start_regions_ru():
    fresh_news = parse_regions_ru("kotelniki")
    for one_news in fresh_news.values():
        #print(one_news)
        news = f"{one_news['link']}\n" \
                f"{one_news['head']}\n" \
                f"{one_news['text']}" 
        await bot.send_message(chat_id=bot_chat_id, text=news, reply_markup=get_inline_keys())


# После нажатие на COMMENT бот забирает последнее сообщение пользователя и пересылает его 
# вместе с ссылкой на новость в указанный чат/канал, затем удаляет кнопки
# Бот должен быть админом в том чате/канале
@dp.callback_query(F.data =='Comment')
async def inline_answer_button_comment(c_q: types.CallbackQuery):
    #article_name = c_q.message.text.split('\n')[1]
    #article_text = '\n'.join(c_q.message.text.split('\n')[2:])
    article_link = c_q.message.text.split('\n')[0]
    news_with_comment =  f'{article_link}\n\n'\
            f'<b><i>{last_message}</i></b>'
    await bot.send_message(chat_id=bot_chat_id, text=news_with_comment)
    await bot.edit_message_reply_markup(
        chat_id=c_q.message.chat.id, 
        message_id=c_q.message.message_id,
        reply_markup=None
    )


# После нажатие на TEXT бот пересылает текст сообщения в указанный чат/канал, затем удаляет кнопки
# Бот должен быть админом в том чате/канале
@dp.callback_query(F.data =='Text')
async def inline_answer_button_text(c_q: types.CallbackQuery):
    article_name = c_q.message.text.split('\n')[1]
    article_text = '\n'.join(c_q.message.text.split('\n')[2:])
    article_link = c_q.message.text.split('\n')[0]
    news_text = f'{article_name} \n\n'  \
            f'{article_text} \n\n'\
            f'<a href="{article_link}">Ссылка</a>'
    await bot.send_message(chat_id=bot_chat_id, text=news_text)
    await bot.edit_message_reply_markup(
        chat_id=c_q.message.chat.id, 
        message_id=c_q.message.message_id,
        reply_markup=None
    )


# После нажатие на Com&Text бот забирает последнее сообщение пользователя и пересылает его 
# вместе с с сообщением бота в указанный чат/канал, затем удаляет кнопки
# Бот должен быть админом в том чате/канале
@dp.callback_query(F.data =='Com&Text')
async def inline_answer_button_comment(c_q: types.CallbackQuery):
    article_name = c_q.message.text.split('\n')[1]
    article_text = '\n'.join(c_q.message.text.split('\n')[2:])
    article_link = c_q.message.text.split('\n')[0]
    news_with_comment = f'{article_name} \n\n'  \
            f'{article_text} \n\n'\
            f'<b><i>{last_message}</i></b> \n'\
            f'<a href="{article_link}">Ссылка</a>'
    await bot.send_message(chat_id=kk_channel_id, text=news_with_comment)
    await bot.edit_message_reply_markup(
        chat_id=c_q.message.chat.id, 
        message_id=c_q.message.message_id,
        reply_markup=None
    )


# После нажатие на YES бот пересылает заголовок сообщения в указанный чат/канал, затем удаляет кнопки
# Бот должен быть админом в том чате/канале
@dp.callback_query(F.data =='Yes')
async def inline_answer_button_yes(c_q: types.CallbackQuery):
    await bot.send_message(chat_id=kk_channel_id, text=c_q.message.text)
    await bot.edit_message_reply_markup(
        chat_id=c_q.message.chat.id, 
        message_id=c_q.message.message_id,
        reply_markup=None
    )


# После нажатие на NO бот только удаляет кнопки, сообщение потом можно переслать вручную
@dp.callback_query(F.data =='No')
async def inline_answer_button_no(c_q: types.CallbackQuery):
    await bot.edit_message_reply_markup(
        chat_id=c_q.message.chat.id, 
        message_id=c_q.message.message_id,
        reply_markup=None
    )


# После нажатие на DELETE бот удаляет всё сообщение
@dp.callback_query(F.data =='Delete')
async def inline_answer_button_no(c_q: types.CallbackQuery):
    await bot.delete_message(
        chat_id=c_q.message.chat.id, 
        message_id=c_q.message.message_id
    )


async def job(message='stuff', n=1):
    print("Asynchronous invocation (%s) of I'm working on:" % n, message)
    

async def scheduler():
    schedule.every().hours.at('00:08').do(start_regions_ru)
#    schedule.every().hours.at('00:39').do(start_updates_ck)
    while True:
        await schedule.run_pending()
        await asyncio.sleep(0.5)

async def on_startup():
    asyncio.create_task(scheduler())


# Initialize Bot instance with a default parse mode which will be passed to all API calls
# And the run events dispatching
async def main() -> None:
    # bot = Bot(token, parse_mode=ParseMode.HTML)
    dp.startup.register(on_startup)
    await dp.start_polling(bot)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())


