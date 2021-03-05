from typing import Optional, Any

from core.proxy import telegram_proxy
from core.utils.commands import c


async def send_text(
        user: Any,
        text: str,
        commands: Optional[c] = None,
):
    await telegram_proxy.send_text(user.id, text, commands)


async def edit_text(
        user: Any,
        text: str,
        message_id: int,
        commands: Optional[c] = None,
):
    await telegram_proxy.edit_text(user.id, text, message_id, commands)


async def send_image(
        user: Any,
        image: bytes,
        text: Optional[str] = None,
        commands: Optional[c] = None,
):
    await telegram_proxy.send_image(user.id, image, text, commands)
