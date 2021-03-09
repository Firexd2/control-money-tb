import traceback

from core.utils.messages import send_text
from core.texts import TXT
from core.objects import User


def exceptions_catcher():

    def wrapper(func):

        async def wrapped(user_id, *args, **kwargs):
                try:
                    return await func(user_id, *args, **kwargs)
                except Exception as e:
                    user = await User.get(id=user_id)
                    print(traceback.print_exc())
                    await send_text(user, traceback.format_exc())

        return wrapped

    return wrapper
