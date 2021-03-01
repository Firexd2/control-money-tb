from typing import Optional, Union

from core.enums import ButtonsTypes


class c:

    def __init__(self, *commands, type: Optional[ButtonsTypes] = ButtonsTypes.keyboard):
        self._commands = [commands]
        self.type = type

    def __iter__(self):
        self._n = 0

        return self

    def __contains__(self, item):
        for group in self._commands:
            for command in group:
                if self.type == ButtonsTypes.keyboard:
                    if command == item:
                        return True
                else:
                    if command[1] == item:
                        return True

        return False

    def __next__(self):
        if self._n < len(self._commands):
            result = self._commands[self._n]
            self._n += 1
            return result
        else:
            raise StopIteration

    def __bool__(self):
        return bool(self._commands)

    def __add__(self, other: Union[tuple, "c", str]):
        if type(other) in (tuple, list):
            self._commands.append(other)
        elif type(other) == str:
            self._commands.append([other])
        else:
            self._commands.extend(other._commands)

        return self
