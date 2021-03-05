from typing import Optional

from core.enums import ButtonsTypes
from core.utils.commands import c
from core.utils.messages import send_text, edit_text
from core.texts import CMND, BTN


async def send_text_with_pagination(user, texts: list, type: str, current_number: Optional[int] = 0,
                                    action: Optional[int] = 'default', message_id: Optional[int] = None,
                                    len_page: Optional[int] = 10) -> None:

    max_page = len(texts) // len_page
    number = current_number
    if action == CMND.pagination_action_to_start:
        if current_number == 0:
            return
        number = 0
    elif action == CMND.pagination_action_to_end:
        if current_number == max_page:
            return
        number = max_page
    elif action == CMND.pagination_action_current_page:
        return
    elif action == CMND.pagination_action_to_prev:
        if current_number == 0:
            return
        number = current_number - 1
    elif action == CMND.pagination_action_to_next:
        if current_number == max_page:
            return
        number = current_number + 1

    commands = c(type=ButtonsTypes.inline)
    commands += [
        (BTN.pagination_to_start,
         f"{CMND.pagination}{CMND.inline_separator}{type}{CMND.inline_separator}{number}{CMND.inline_separator}"
         f"{CMND.pagination_action_to_start}{CMND.inline_separator}{len_page}"),

        (BTN.pagination_to_prev,
         f"{CMND.pagination}{CMND.inline_separator}{type}{CMND.inline_separator}{number}{CMND.inline_separator}"
         f"{CMND.pagination_action_to_prev}{CMND.inline_separator}{len_page}"),

        (f"-{number + 1}-",
         f"{CMND.pagination}{CMND.inline_separator}{type}{CMND.inline_separator}{number}{CMND.inline_separator}"
         f"{CMND.pagination_action_current_page}{CMND.inline_separator}{len_page}"),

        (BTN.pagination_to_next,
         f"{CMND.pagination}{CMND.inline_separator}{type}{CMND.inline_separator}{number}{CMND.inline_separator}"
         f"{CMND.pagination_action_to_next}{CMND.inline_separator}{len_page}"),

        (BTN.pagination_to_end,
         f"{CMND.pagination}{CMND.inline_separator}{type}{CMND.inline_separator}{number}{CMND.inline_separator}"
         f"{CMND.pagination_action_to_end}{CMND.inline_separator}{len_page}")
    ]

    result_text = "".join([o for o in texts[0 + (number * len_page):len_page + (number * len_page)]])
    if not result_text:
        await send_text(user, "Записей нет")
        return

    if message_id is None:
        await send_text(user, result_text, commands)
    else:
        await edit_text(user, result_text, message_id, commands)
