from aiogram import types
from aiogram.utils import executor

from core import dp, db, bot, config
from core.cache import user_cache
from core.process import process, start_game, inline
from core.utils.common import get_kwargv


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
    resp = await inline(query.from_user.id, query)
    await query.answer(resp)


@dp.message_handler()
async def main_handler(message: types.Message):
    await process(message.from_user["id"], message.text)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    # insert code here to run it after start


async def on_shutdown(dp):
    await bot.delete_webhook()

if __name__ == '__main__':
    if get_kwargv("webhook"):

        WEBHOOK_URL = f"{config['webhook']['host']}{config['webhook']['path']}"

        executor.start_webhook(
            dispatcher=dp,
            webhook_path=config['webhook']['path'],
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=config['webhook']['app_host'],
            port=config['webhook']['app_port'],
        )

    else:
        executor.start_polling(dp, skip_updates=True)
