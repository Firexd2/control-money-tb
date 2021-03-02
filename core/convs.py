from core.enums import ButtonsTypes
from core.objects import Project, ExpenseRecord
from core.texts import BTN, TXT, CMND
from core.utils.commands import split_list_into_sm_lists, c
from core.utils.common import Conv
from core.utils.messages import send_text


def its_start_conv(user, command):
    for conv in registered_convs:
        if conv.this_is(user, command):
            return conv


class CreateProject(Conv):

    command = BTN.create_project

    dont_check_input_in_state = [1]

    async def _state_0(self, *args):
        return True, TXT.create_project_name_question, self._get_commands()

    async def _state_1(self, title):
        project = await Project.create({"title": title})
        project._parent = self.user
        self.user.projects.append(project)
        self.user.current_project = str(project._id)
        await self.user.save()

        return True, TXT.ok, False, True


class SelectProject(Conv):

    command = BTN.select_project

    async def _state_0(self, *args):
        return True, TXT.what_project, self._get_commands(
            *split_list_into_sm_lists([p.title for p in self.user.projects], len_sm_list=3)
        )

    async def _state_1(self, title):
        for p in self.user.projects:
            if p.title == title:
                self.user.current_project = str(p._id)
                await self.user.save()

                return True, TXT.ok, False, True


class WithdrawMoney(Conv):

    command = BTN.withdraw_money

    dont_check_input_in_state = [1, 2, 3]

    @classmethod
    def this_is(cls, user, command):
        return command == cls.command and user.get_current_project()

    def get_tags_as_inline_commands(self):
        r = c(type=ButtonsTypes.inline)
        for row in split_list_into_sm_lists(
            [(tag, f"{CMND.append_tag}{CMND.inline_separator}{tag}") for tag in self.user.tags_used], len_sm_list=3
        ):
            r += row

        return r

    async def _state_0(self, *args):
        self._tags = []

        await send_text(self.user, TXT.recently_used_tags, self.get_tags_as_inline_commands())

        return True, TXT.select_tags_or_type_new, self._get_commands(BTN.complete_select_tags)

    async def _state_1(self, command):

        if command == BTN.complete_select_tags:
            return True, "Цена?", self._get_commands()
        else:
            if command not in self._tags:
                self._tags.append(command)

            selected_tags = ",".join(self._tags)
            await send_text(self.user, TXT.recently_used_tags, self.get_tags_as_inline_commands())

            return False, f"{TXT.selected_tags}\n{selected_tags}", None

    async def _state_2(self, value):
        try:
            int(value)
        except ValueError:
            return False, TXT.only_digits, None

        return True, TXT.what_comment, self._get_commands(BTN.no_comments)

    async def _state_3(self, comment):

        project = self.user.get_current_project()

        value = int(self._selected_commands[-1])

        project.free_money -= value

        for t in self._tags:
            if t not in self.user.tags_used:
                self.user.tags_used.append(t)

        expense_record = ExpenseRecord(tags=self._tags, value=value, comment=comment)
        expense_record._parent = project

        project.expense_records.append(expense_record)

        await self.user.save()

        return True, TXT.ok, False, True


class AboutProject(Conv):

    command = BTN.about_project

    @classmethod
    def this_is(cls, user, command):
        return command == cls.command and user.get_current_project()

    async def _state_0(self, *args):
        project = self.user.get_current_project()
        last_records = '\n\n'.join([f"<i>{', '.join(r.tags)}</i>\n{r.comment}\n{r.value} р." for r in project.expense_records])
        text = f"""
Свободные деньги <b>{project.free_money}</b>

Последние траты:
{last_records}
"""

        return True, text, False, True


registered_convs = [CreateProject, SelectProject, WithdrawMoney, AboutProject]
