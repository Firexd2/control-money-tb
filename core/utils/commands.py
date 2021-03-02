from typing import Optional, Union

from core.enums import ButtonsTypes


def split_list_into_sm_lists(commands, len_sm_list):
    result = []
    for n, command in enumerate(commands):
        row = n // len_sm_list
        if len(result) != row + 1:
            result.append([])

        result[-1].append(command)

    return result


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

    def __len__(self):
        result = 0
        for gr in self._commands:
            result += len(gr)

        return result
