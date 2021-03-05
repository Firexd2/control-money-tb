from core.convs import its_start_conv
from core.objects import User
from core.texts import TXT, CMND
from core.utils.decorators import exceptions_catcher
from core.utils.messages import send_text
from core.utils.pagination import send_text_with_pagination


async def start_game(data):
    user = await User.get(id=data["id"])
    if not user:
        del data["is_bot"]
        if "language_code" in data:
            del data["language_code"]
        user = await User.create(data)

        text, commands = "Ты зареган", await user.get_commands()
    else:
        text, commands = "зачем тебе start?", await user.get_commands()

    await send_text(user, text, commands)


@exceptions_catcher()
async def process(user_id: int, message: str):
    user = await User.get(id=user_id)

    if CMND.join in message:
        await user.join_project(message)
    elif CMND.delete in message:
        await user.delete_record(message)
    elif user._conv is not None:
        await user.conv_exec(message)
    elif (conv := await its_start_conv(user, message)):
        await user.conv_start(conv)
    else:
        await user.process(message)


@exceptions_catcher()
async def inline(user_id, query):
    message = query.data
    user = await User.get(id=user_id)
    resp = TXT.ok

    if CMND.append_tag in message:
        tag = message.split(CMND.inline_separator)[-1]
        if tag not in user._conv._tags:
            user._conv._tags.append(tag)

        await send_text(user, user._conv.get_text_selected_tags())

    if CMND.pagination in message:
        type, number, action, len_page = message.split(CMND.inline_separator)[1:]

        if CMND.pagination_expense_for_project == type:
            project = await user.get_current_project()
            objects = await project.get_expense_records()
            texts = [str(o) for o in objects]
        elif CMND.pagination_expense_for_plan:
            project = await user.get_current_project()
            plans = await project.get_current_plan()
            objects = await plans.get_expense_records()
            texts = [str(o) for o in objects]

        await send_text_with_pagination(
            user, texts, type, action=action, current_number=int(number), message_id=query.message.message_id,
            len_page=int(len_page)
        )

    return resp
