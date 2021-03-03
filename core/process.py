from core.convs import its_start_conv
from core.objects import User
from core.texts import TXT, CMND
from core.utils.decorators import exceptions_catcher
from core.utils.messages import send_text


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

    if user._conv is not None:
        await user.conv_exec(message)
    elif (conv := await its_start_conv(user, message)):
        await user.conv_start(conv)
    else:
        await user.process(message)


@exceptions_catcher()
async def inline(user_id: int, message: str):
    user = await User.get(id=user_id)
    resp = TXT.ok

    if CMND.append_tag in message:
        tag = message.split(CMND.inline_separator)[-1]
        if tag not in user._conv._tags:
            user._conv._tags.append(tag)

        selected_tags = ",".join(user._conv._tags)

        await send_text(user, f"{TXT.selected_tags}\n{selected_tags}")

    return resp
