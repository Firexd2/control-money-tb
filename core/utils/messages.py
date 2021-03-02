from typing import Optional, Any

from core.utils.commands import c
from core.proxy import telegram_proxy


async def send_text(
        user: Any,
        text: str,
        commands: Optional[c] = None,
):
    await telegram_proxy.send_text(user.id, text, commands)


async def send_image(
        user: Any,
        image: bytes,
        text: Optional[str] = None,
        commands: Optional[c] = None,
):
    await telegram_proxy.send_image(user.id, image, text, commands)
