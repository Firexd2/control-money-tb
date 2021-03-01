from core.convs import its_start_conv
from core.utils.decorators import exceptions_catcher
from core.utils.messages import send_text
from core.objects import User

async def start_game(data):
    user = await User.get(id=data["id"])
    if not user:
        del data["is_bot"]
        if "language_code" in data:
            del data["language_code"]
        await User.create(data)
        user = await User.get(id=data["id"])

        text, commands = "create user", user.get_commands()
    else:
        text, commands = "test", user.get_commands()

    await send_text(user, text, commands)


@exceptions_catcher()
async def process(user_id: int, message: str):
    user = await User.get(id=user_id)

    if user._conv is not None:
        await user.conv_exec(message)
    elif (conv := its_start_conv(user, message)):
        await user.conv_start(conv)
