from aiogram import types
from aiogram.utils import executor

from core import dp, db
from core.cache import user_cache
from core.process import process, start_game, inline


@dp.message_handler(commands="drop")
async def drop_handler(message: types.Message):
    await db.command("dropDatabase")
    user_cache.clear()
    await message.answer("ok")


@dp.message_handler(commands="start")
async def start_handler(message: types.Message):
    await start_game(dict(message.from_user))


@dp.callback_query_handler()
async def inline_callback_handler(query: types.CallbackQuery):
    answer_data = query.data
    user_id = query.from_user.id
    resp = await inline(user_id, answer_data)
    await query.answer(resp)


@dp.message_handler()
async def main_handler(message: types.Message):
    await process(message.from_user["id"], message.text)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
