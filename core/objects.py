from typing import Optional, Union

from core.cache import user_cache
from core.texts import BTN, TXT
from core.utils.commands import c
from core.utils.common import ConvType
from core.utils.db import Database, Field, IntField, StrField, ManyOfOneField, Model, ListField
from core.utils.messages import send_text


class ExpenseRecord(Model):
    tags = ListField(default=list)
    value = IntField()
    comment = StrField()


class Project(Database):
    _id = Field()

    title = StrField()

    free_money = IntField(default=0)
    expense_records = ManyOfOneField(ExpenseRecord, default=list)

    def get_commands(self):
        commands = c()
        commands += BTN.withdraw_money,
        commands += ("Выбрать план", "Создать план")
        commands += (BTN.about_project, BTN.leave_project)

        return commands

    async def process(self, command):
        if command == BTN.leave_project:
            user = self._parent
            user.current_project = None
            await user.save()

            await send_text(user, TXT.leave_project, user.get_commands())
        else:
            await send_text(self._parent, TXT.unknown, self.get_commands())


class User(Database):
    _id = Field()
    id = IntField()
    projects = ManyOfOneField(Project, default=list)
    current_project = StrField(default=None)
    tags_used = ListField(default=list)

    _conv: Optional[ConvType] = None

    cache_objects = {"search_by": "id", "object": user_cache}

    def get_commands(self):
        if self.current_project is None:
            return c(BTN.select_project, BTN.create_project)
        else:
            project = self.get_current_project()

            return project.get_commands()

    def get_current_project(self) -> Union[Project, None]:
        for p in self.projects:
            if str(p._id) == self.current_project:
                return p

        raise Exception(TXT.have_no_projects)

    async def conv_start(self, conv, *args):
        self._conv = conv(self, *args)
        text, command = await self._conv.start()
        await send_text(self, text, command)

    async def conv_exec(self, message):
        text, command = await self._conv.process(message)
        if text is not None:
            await send_text(self, text, command)

    async def process(self, command):
        if self.current_project:
            project = self.get_current_project()
            await project.process(command)
        else:
            await send_text(self, TXT.unknown, self.get_commands())
