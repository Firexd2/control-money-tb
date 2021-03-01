from typing import Optional, Any

from core.utils.commands import c
from core.proxy import telegram_proxy


async def send_text(
        object: Any,
        text: str,
        commands: Optional[c] = None,
        commands_by_status: Optional[bool] = False
):
    print(commands)
    await telegram_proxy.send_text(
        object.id,
        text,
        commands if not commands_by_status else object.get_commands()
    )
    if commands_by_status:
        object._conv = None


async def send_image(
        object: Any,
        image: bytes,
        text: Optional[str] = None,
        commands: Optional[c] = None,
        commands_by_status: Optional[bool] = False
):
    await telegram_proxy.send_image(
        object.id,
        image,
        text,
        commands if not commands_by_status else object.get_commands()
    )
    if commands_by_status:
        object._conv = None
