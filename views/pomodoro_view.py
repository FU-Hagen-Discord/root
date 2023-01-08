import discord
from discord import ButtonStyle, Interaction
from discord.ui import Button, View

from models import Timer, TimerAttendee


class PomodoroView(View):
    def __init__(self, pomodoro):
        super().__init__(timeout=None)
        self.pomodoro = pomodoro

    @discord.ui.button(label="Anmelden", emoji="👍", style=ButtonStyle.green, custom_id="timerview:subscribe")
    async def btn_subscribe(self, interaction: Interaction, button: Button):
        await interaction.response.defer(ephemeral=True, thinking=False)
        if timer := Timer.get_or_none(Timer.message == interaction.message.id):
            if TimerAttendee.get_or_none(TimerAttendee.timer == timer.id, TimerAttendee.member == interaction.user.id):
                await interaction.followup.send(content="Du bist bereits angemeldet.", ephemeral=True)
                return

            TimerAttendee.create(timer=timer.id, member=interaction.user.id)
            embed = timer.create_embed()
            await interaction.message.edit(embed=embed, view=self)
            await interaction.followup.send(content="Du hast dich erfolgreich angemeldet", ephemeral=True)
        else:
            await interaction.followup.send(content="Etwas ist schiefgelaufen...", ephemeral=True)

    @discord.ui.button(label="Abmelden", emoji="👎", style=ButtonStyle.red, custom_id="timerview:unsubscribe")
    async def btn_unsubscribe(self, interaction: Interaction, button: Button):
        await interaction.response.defer(ephemeral=True, thinking=False)
        if timer := Timer.get_or_none(Timer.message == interaction.message.id):
            if timer_attendee := TimerAttendee.get_or_none(TimerAttendee.timer == timer.id,
                                                           TimerAttendee.member == interaction.user.id):
                timer_attendee.delete_instance()
                if TimerAttendee.select().where(TimerAttendee.timer == timer.id).count() > 0:
                    embed = timer.create_embed()
                    await interaction.message.edit(embed=embed, view=self)
                else:
                    await self.pomodoro.switch_phase(timer, new_status_idx=-1)
                await interaction.followup.send(content="Du hast dich erfolgreich abgemeldet", ephemeral=True)
            else:
                await interaction.followup.send(content="Du musst erst angemeldet sein, um dich abmelden zu "
                                                        "können.", ephemeral=True)
        else:
            await interaction.followup.send(content="Etwas ist schiefgelaufen...", ephemeral=True)

    @discord.ui.button(label="Phase überspringen", emoji="⏩", style=ButtonStyle.blurple, custom_id="timverview:skip")
    async def btn_skip(self, interaction: Interaction, button: Button):
        await interaction.response.defer(ephemeral=True, thinking=False)
        if timer := Timer.get_or_none(Timer.message == interaction.message.id):
            if TimerAttendee.get_or_none(TimerAttendee.timer == timer.id, TimerAttendee.member == interaction.user.id):
                new_phase = await self.pomodoro.switch_phase(timer)
                await interaction.followup.send(content="Erfolgreich übersprungen", ephemeral=True)
                return

            await interaction.followup.send(content="Nur angemeldete Personen können den Timer bedienen.",
                                            ephemeral=True)
            return

        await interaction.followup.send(content="Etwas ist schiefgelaufen...", ephemeral=True)

    @discord.ui.button(label="Neustarten", emoji="🔄", style=ButtonStyle.blurple, custom_id="timverview:restart")
    async def btn_restart(self, interaction: Interaction, button: Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        if timer := Timer.get_or_none(Timer.message == interaction.message.id):
            if TimerAttendee.get_or_none(TimerAttendee.timer == timer.id, TimerAttendee.member == interaction.user.id):
                new_phase = await self.pomodoro.switch_phase(timer, new_status_idx=0)
                await interaction.followup.send(content="Erfolgreich neugestartet", ephemeral=True)
                return

            await interaction.followup.send(content="Nur angemeldete Personen können den Timer bedienen.",
                                            ephemeral=True)
            return

        await interaction.followup.send(content="Etwas ist schiefgelaufen...", ephemeral=True)

    @discord.ui.button(label="Beenden", emoji="🛑", style=ButtonStyle.grey, custom_id="timverview:stop")
    async def btn_stop(self, interaction: Interaction, button: Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        if timer := Timer.get_or_none(Timer.message == interaction.message.id):
            if TimerAttendee.get_or_none(TimerAttendee.timer == timer.id, TimerAttendee.member == interaction.user.id):
                new_phase = await self.pomodoro.switch_phase(timer, new_status_idx=-1)
                await interaction.followup.send(content="Erfolgreich neugestartet", ephemeral=True)
                return

            await interaction.followup.send(content="Nur angemeldete Personen können den Timer bedienen.",
                                            ephemeral=True)
            return

        await interaction.followup.send(content="Etwas ist schiefgelaufen...", ephemeral=True)

    def disable(self):
        for button in self.children:
            button.disabled = True
