import logging

from aiogram import Bot, Dispatcher
import motor.motor_asyncio

from core.utils.common import get_config


def init() -> tuple:

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    config = get_config()

    bot = Bot(token=config['token'])
    dp = Dispatcher(bot)
    client = motor.motor_asyncio.AsyncIOMotorClient(host=config["mongo"]["host"])
    db = client[config["mongo"]["name"]]

    return bot, dp, db, config



bot, dp, db, config = init()
