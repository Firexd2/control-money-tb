import argparse
import os
import pathlib
from typing import Any
from typing import Optional, TypeVar, List

import trafaret
from aiogram import types
from aiogram.types import ReplyKeyboardRemove
from trafaret_config import commandline

from core.enums import ButtonsTypes
from core.texts import BTN, TXT
from core.utils.commands import c

PATH = pathlib.Path(__file__).parent.parent

settings_file = os.environ.get('SETTINGS_FILE', 'app.yml')
DEFAULT_CONFIG_PATH = PATH / 'config' / settings_file


CONFIG_TRAFARET = trafaret.Dict({
    "token": trafaret.String(),
    trafaret.Key('proxy', optional=True):
        trafaret.Dict({
            'url': trafaret.String(),
            'username': trafaret.String(),
            'password': trafaret.String()
        }),
    trafaret.Key('mongo'):
        trafaret.Dict({
            'host': trafaret.String()
        }),
})


def get_config() -> Any:
    argv = ['-c', DEFAULT_CONFIG_PATH.as_posix()]

    ap = argparse.ArgumentParser()
    commandline.standard_argparse_options(
        ap,
        default_config=DEFAULT_CONFIG_PATH,
    )
    config = commandline.config_from_options(ap.parse_args(argv), CONFIG_TRAFARET)

    return config


def get_buttons(commands):
    commands_kw = {}
    if commands:
        if commands.type == ButtonsTypes.keyboard:
            keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for row in commands:
                keyboard_markup.row(*[types.KeyboardButton(text) for text in row])

            commands_kw = {"reply_markup": keyboard_markup}
        elif commands.type == ButtonsTypes.inline:
            inline_markup = types.InlineKeyboardMarkup(resize_keyboard=True)
            for row in commands:
                inline_markup.row(*[types.InlineKeyboardButton(text, callback_data=command) for text, command in row])

            commands_kw = {"reply_markup": inline_markup}
    elif commands is False:
        commands_kw = {"reply_markup": ReplyKeyboardRemove()}

    return commands_kw




class Conv:
    """
    Каждый _state_* должен содержать в return три обязательных аргумента (успешность, текст, команды),
    и один опциональный (конец беседы)
    """
    command = None

    @classmethod
    def this_is(cls, user, command):
        return command == cls.command

    def __init__(self, user):
        self.user = user
        self._state = 0
        # последние выбранные команды
        self._selected_commands: list = list()
        # все предложенные команды
        self._commands: List[c] = list()
        # контекст state'ов
        self._last_ctxs: list = list()

    async def process(self, message):
        if message != BTN.back:
            text, command = await self._next(message)
        else:
            text, command = await self._back()

        return text, command

    async def start(self):
        text, commands = await self._next(its_start=True)

        return text, commands

    def _get_commands(self, *args):
        commands = c()
        for arg in args:
            commands += arg

        return commands + BTN.back

    async def _next(self, command: Optional[str] = None, its_start: Optional[bool] = False):
        if its_start:
            success, text, commands, *end = await self._state_0()
        else:
            if command not in self._commands[-1]:
                return TXT.unknown, None

            success, text, commands, *end = await getattr(self, f"_state_{str(self._state + 1)}")(command)

        if commands is False:
            commands = self.user.get_commands()

        if success and not its_start:
            self._selected_commands.append(command)
            self._state += 1
            if len(self._last_ctxs) == self._state - 1:
                self._last_ctxs.append(None)

        if success:
            self._commands.append(commands)

        if end and end[0]:
            self.user._conv = None

        return text, commands

    async def _back(self):
        self._state -= 1

        if self._state < 0:
            self.user._conv = None

            return TXT.you_have_leaved_conv, self.user.get_commands()

        del self._last_ctxs[-1:-3:-1]
        del self._selected_commands[-1]
        del self._commands[-1]
        command = None
        if self._selected_commands:
            command = self._selected_commands[-1]

        _, text, commands = await getattr(self, f"_state_{str(self._state)}")(command)

        return text, commands

    async def _state_0(self, *args):
        raise NotImplementedError


ConvType = TypeVar('ConvType', bound=Conv)
