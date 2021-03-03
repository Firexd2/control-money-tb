from typing import Any, Union

from aiogram.types import ParseMode

from core import bot
from core.utils.common import get_buttons


class TelegramProxy():

    async def send_text(self, chat_id: int, text: str, commands: Any):
        commands_kw = get_buttons(commands)

        if len(text) > 4096:
            for x in range(0, len(text), 4096):
                await bot.send_message(chat_id, text[x:x + 4096], **commands_kw, parse_mode=ParseMode.HTML)
        else:
            await bot.send_message(chat_id, text, **commands_kw, parse_mode=ParseMode.HTML)

    async def send_image(self, chat_id: int, image: bytes, text: str, commands: Any):
        commands_kw = get_buttons(commands)

        await bot.send_photo(chat_id, image, caption=text, **commands_kw, parse_mode=ParseMode.HTML)


telegram_proxy = TelegramProxy()
