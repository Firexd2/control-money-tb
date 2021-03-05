import datetime
from typing import Optional, Union, List

from bson import ObjectId

from core.cache import user_cache
from core.texts import BTN, TXT, CMND
from core.utils.commands import c
from core.utils.common import ConvType
from core.utils.db import Database, Field, IntField, StrField, ListField
from core.utils.messages import send_text


class ExpenseRecord(Database):
    _id = Field()
    tags = ListField(default=list)
    parent_id = Field()
    value = IntField()
    comment = StrField()
    datetime = Field()

    def __str__(self):
        return f"""
⏱ <b>{self.datetime.strftime("%d.%m.%Y %H:%M:%S")}</b>
🔖 <i>{', '.join(self.tags)}</i> 💰 {self.value} р.
💬 {self.comment}
/{CMND.delete}{CMND.separator}{str(self._id)}
"""


class Plan(Database):
    _id = Field()

    title = StrField()

    money = IntField(default=0)

    start_date = Field(default=datetime.datetime.now)
    start_money = IntField(default=0)

    def __str__(self):
        return f"""
<b>План:</b>
🔹 {self.title}
🕐 {self.start_date.strftime("%d.%m.%Y")}
💰 {self.money} / {self.start_money}
💸 {int((self.start_money - self.money) / ((datetime.datetime.now().date() - self.start_date.date()).days + 1))} в день
"""

    async def get_commands(self):
        commands = c()
        commands += BTN.make_payment,
        commands += (BTN.about_plan, BTN.leave_plan)

        return commands

    async def get_expense_records(self) -> List[ExpenseRecord]:
        return await ExpenseRecord.filter({"parent_id": self._id})

    async def process(self, user, command):
        if command == BTN.leave_plan:
            project = await user.get_current_project()
            project.current_plan_id = None
            await project.save()
            await send_text(user, TXT.leave_project, await user.get_commands())
        else:
            await send_text(user, TXT.unknown, await self.get_commands())


class Project(Database):
    _id = Field()

    title = StrField()

    tags_used = ListField(default=list)

    money = IntField(default=0)

    plans_ids = ListField(default=list)
    current_plan_id = Field(default=None)

    async def get_str(self):
        money_in_plans = sum([p.money for p in await self.get_plans()])

        return f"""
<b>Проект:</b>
🔹 {self.title}
💵 Свободные: <b>{self.money}</b>
💸 В обороте: <b>{money_in_plans}</b>
💰 Всего: <b>{money_in_plans + self.money}</b>

Чтобы присоединиться к проекту, отправь команду:
/{CMND.join}{CMND.separator}{str(self._id)}
"""

    async def get_commands(self):
        if not self.current_plan_id:
            commands = c()
            commands += (BTN.select_plan, BTN.create_plan)
            commands += (BTN.withdraw_money, BTN.make_income)
            commands += (BTN.about_project, BTN.leave_project)

            return commands
        else:
            plan = await self.get_current_plan()

            return await plan.get_commands()

    async def get_plans(self) -> List[Plan]:
        return await Plan.filter({"_id": {"$in": self.plans_ids}})

    async def get_current_plan(self) -> Union[Plan, None]:
        for p in await self.get_plans():
            if p._id == self.current_plan_id:
                return p

        raise Exception(TXT.have_no_projects)

    async def get_expense_records(self) -> List[ExpenseRecord]:
        return await ExpenseRecord.filter({"parent_id": self._id})

    async def process(self, user, command):
        if self.current_plan_id:
            plan = await self.get_current_plan()
            await plan.process(user, command)

        elif command == BTN.leave_project:
            user.current_project_id = None
            await user.save()
            await send_text(user, TXT.leave_project, await user.get_commands())

        else:
            await send_text(user, TXT.unknown, await self.get_commands())


class User(Database):
    _id = Field()
    id = IntField()
    first_name = StrField()
    projects_ids = ListField(default=list)
    current_project_id = Field(default=None)

    _conv: Optional[ConvType] = None

    cache_objects = {"search_by": "id", "object": user_cache}

    async def get_commands(self):
        if self.current_project_id is None:
            return c(BTN.select_project, BTN.create_project)
        else:
            project = await self.get_current_project()

            return await project.get_commands()

    async def get_projects(self) -> List[Project]:
        return await Project.filter({"_id": {"$in": self.projects_ids}})

    async def get_current_project(self) -> Union[Project, None]:
        for p in await self.get_projects():
            if p._id == self.current_project_id:
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

    async def join_project(self, message):
        id = ObjectId(message.split(CMND.separator)[-1])

        if id not in self.projects_ids:
            self.projects_ids.append(id)

            await self.save()

            await send_text(self, TXT.ok)

        else:
            await send_text(self, TXT.project_already_exist)

    async def delete_record(self, message):
        id = ObjectId(message.split(CMND.separator)[-1])

        record = await ExpenseRecord.get(_id=id)
        object = await Plan.get(_id=record.parent_id) or await Project.get(_id=record.parent_id)
        object.money += record.value
        await object.save()
        await record.delete()

        await send_text(self, TXT.ok)

    async def process(self, command):
        if self.current_project_id:
            project = await self.get_current_project()
            await project.process(self, command)
        else:
            await send_text(self, TXT.unknown, await self.get_commands())
