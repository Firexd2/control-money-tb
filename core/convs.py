import datetime

import pytz

from core.enums import ButtonsTypes
from core.objects import Project, ExpenseRecord, Plan
from core.texts import BTN, TXT, CMND
from core.utils.commands import split_list_into_sm_lists, c
from core.utils.common import Conv
from core.utils.messages import send_text


moscowtz = pytz.timezone('Europe/Moscow')


async def its_start_conv(user, command):
    for conv in registered_convs:
        if await conv.this_is(user, command):
            return conv


class CreateProject(Conv):

    command = BTN.create_project

    dont_check_input_in_state = [1]

    async def _state_0(self, *args):
        return True, TXT.create_name_question, self._get_commands()

    async def _state_1(self, title):
        project = await Project.create({"title": title})
        self.user.projects_ids.append(project._id)
        self.user.current_project_id = project._id
        await self.user.save()

        return True, TXT.ok, False, True


class SelectProject(Conv):

    command = BTN.select_project

    async def _state_0(self, *args):
        projects = await self.user.get_projects()
        if projects:
            return True, TXT.what_project, self._get_commands(
                *split_list_into_sm_lists([p.title for p in projects], len_sm_list=3)
            )
        else:
            return False, TXT.have_no_projects, False, True

    async def _state_1(self, title):
        projects = await self.user.get_projects()
        for p in projects:
            if p.title == title:
                self.user.current_project_id = p._id
                await self.user.save()

                return True, TXT.ok, False, True


class MakePaymentBase(Conv):

    async def get_object(self):
        raise NotImplementedError()

    dont_check_input_in_state = [1, 2, 3]

    @classmethod
    async def this_is(cls, user, command):
        return command == cls.command and await user.get_current_project()

    async def get_tags_as_inline_commands(self):
        r = c(type=ButtonsTypes.inline)
        project = await self.user.get_current_project()
        for row in split_list_into_sm_lists(
            [(tag, f"{CMND.append_tag}{CMND.inline_separator}{tag}") for tag in project.tags_used], len_sm_list=3
        ):
            r += row

        return r

    async def send_recently_tags(self):
        recently_tags = await self.get_tags_as_inline_commands()
        if recently_tags:
            await send_text(self.user, TXT.recently_used_tags, recently_tags)

    async def _state_0(self, *args):
        self._tags = []

        await self.send_recently_tags()

        return True, TXT.select_tags_or_type_new, self._get_commands(BTN.complete_select_tags)

    async def _state_1(self, command):

        if command == BTN.complete_select_tags:
            return True, "Цена?", self._get_commands()
        else:
            if command not in self._tags:
                self._tags.append(command)

            await self.send_recently_tags()

            selected_tags = ",".join(self._tags)
            return False, f"{TXT.selected_tags}\n{selected_tags}", None

    async def _state_2(self, value):
        try:
            int(value)
        except ValueError:
            return False, TXT.only_digits, None

        return True, TXT.what_comment, self._get_commands(BTN.no_comments)

    async def _state_3(self, comment):

        object = await self.get_object()

        value = int(self._selected_commands[-1])

        object.money -= value

        await ExpenseRecord.create({
            "tags": self._tags, "value": value, "comment": comment, "parent_id": object._id,
            "datetime": datetime.datetime.now()
        })

        await object.save()

        project = await self.user.get_current_project()
        for t in self._tags:
            if t in project.tags_used:
                project.tags_used.remove(t)

            project.tags_used.append(t)

        await project.save()

        return True, TXT.ok, False, True


class WithdrawMoney(MakePaymentBase):

    command = BTN.withdraw_money

    async def get_object(self):
        return await self.user.get_current_project()


class MakePayment(MakePaymentBase):

    command = BTN.make_payment

    async def get_object(self):
        project = await self.user.get_current_project()

        return await project.get_current_plan()


class AboutProject(Conv):

    command = BTN.about_project

    @classmethod
    async def this_is(cls, user, command):
        return command == cls.command and await user.get_current_project()

    async def _state_0(self, *args):
        project = await self.user.get_current_project()
        records = await project.get_expense_records()
        last_records = '\n\n'.join([f"{r.datetime.isoformat()}\n<i>{', '.join(r.tags)}</i>\n{r.comment}\n{r.value} р." for r in records])
        text = f"""
Свободные деньги <b>{project.money}</b>

Последние траты:
{last_records}
"""

        return True, text, False, True


class CreatePlan(Conv):

    command = BTN.create_plan

    dont_check_input_in_state = [1]

    async def _state_0(self, *args):
        return True, TXT.create_name_question, self._get_commands()

    async def _state_1(self, title):
        project = await self.user.get_current_project()

        plan = await Plan.create({"title": title})

        project.current_plan_id = plan._id
        project.plans_ids.append(plan._id)

        await project.save()

        return True, TXT.ok, False, True


class SelectPlan(Conv):

    command = BTN.select_plan

    async def _state_0(self, *args):
        project = await self.user.get_current_project()
        plans = await project.get_plans()
        if plans:
            return True, TXT.what_project, self._get_commands(
                *split_list_into_sm_lists([p.title for p in plans], len_sm_list=3)
            )
        else:
            return False, TXT.have_no_plans, False, True

    async def _state_1(self, title):
        project = await self.user.get_current_project()
        plans = await project.get_plans()
        for p in plans:
            if p.title == title:
                project.current_plan_id = p._id
                await project.save()

                return True, str(p), False, True


class AboutPlan(Conv):

    command = BTN.about_plan

    dont_check_input_in_state = [2]

    async def get_exit_text(self):
        project = await self.user.get_current_project()
        plan = await project.get_current_plan()

        return str(plan)

    @classmethod
    async def this_is(cls, user, command):
        return command == cls.command and await user.get_current_project()

    async def _state_0(self, *args):
        project = await self.user.get_current_project()
        plan = await project.get_current_plan()

        return True, str(plan), self._get_commands([BTN.all_expense_records, BTN.new_period])

    async def _state_1(self, command):
        if command == BTN.all_expense_records:
            project = await self.user.get_current_project()
            plan = await project.get_current_plan()

            return False, "".join([str(r) for r in await plan.get_expense_records()]) or "Трат нет", None
        elif command == BTN.new_period:
            return True, TXT.what_value_for_new_plan, self._get_commands()

    async def _state_2(self, value):
        try:
            value = int(value)
        except ValueError:
            return False, TXT.only_digits, None

        project = await self.user.get_current_project()
        plan = await project.get_current_plan()

        project.money += plan.money

        records = await ExpenseRecord.filter({"parent_id": plan._id})
        for r in records:
            r.parent_id = project._id
            await r.save()

        plan.money = value
        plan.start_money = value
        plan.start_date = datetime.datetime.now()
        project.money -= value

        await plan.save()
        await project.save()

        return True, TXT.ok, False, True


registered_convs = [CreateProject, SelectProject, WithdrawMoney, AboutProject, CreatePlan, SelectPlan,
                    AboutPlan, MakePayment]
