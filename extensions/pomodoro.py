import asyncio
import random
from typing import List

import discord
from discord import Interaction, app_commands, Guild, VoiceChannel
from discord.ext import commands, tasks

from models import Timer, TimerAttendee
from views.pomodoro_view import PomodoroView

STATUS = ["Arbeiten", "Pause", "Beendet"]


def get_soundfile(status: str):
    return {
        "Arbeiten": "roll_with_it-outro.mp3",
        "Pause": "groove-intro.mp3",
        "Beendet": "applause.mp3"
    }.get(status)


def get_remaining(timer, new_status):
    if new_status == STATUS[0]:
        return timer.working_time
    return timer.break_time


def get_mentions(timer: Timer):
    return ", ".join(
        [f"<@{attendee.member}>" for attendee in TimerAttendee.select().where(TimerAttendee.timer == timer.id)])


async def get_voice_channels(guild: Guild, attendees: List[TimerAttendee]):
    voice_channels = {}
    for attendee in attendees:
        member = await guild.fetch_member(attendee.member)
        if vc := member.voice:
            voice_channels[vc.channel.id] = vc.channel

    return voice_channels


async def play_sound(voice_channel: VoiceChannel, filename: str):
    try:
        voice_client = await voice_channel.connect()
        voice_client.play(discord.FFmpegPCMAudio(f'sounds/{filename}'))
        while voice_client.is_playing():
            await asyncio.sleep(1)
        await voice_client.disconnect()
    except discord.errors.ClientException as e:
        print(e)


@app_commands.guild_only()
class Pomodoro(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config["extensions"][__name__.split(".")[-1]]
        self.default_names = self.config["default_names"]
        self.run_timer.start()

    @app_commands.command(name="timer", description="Erstelle deine persönliche Eieruhr")
    async def cmd_timer(self, interaction: Interaction, working_time: int = 25, break_time: int = 5, name: str = None):
        await interaction.response.defer()
        message = await interaction.original_response()
        name = random.choice(self.default_names) if not name else name
        remaining = working_time
        status = STATUS[0]

        timer = Timer.create(name=name, status=status, working_time=working_time, break_time=break_time,
                             remaining=remaining, channel=interaction.channel_id, message=message.id,
                             guild=interaction.guild.id)
        TimerAttendee.create(timer=timer.id, member=interaction.user.id)
        embed = timer.create_embed()
        await interaction.edit_original_response(embed=embed, view=self.get_view())
        await self.send_acoustic_notification(timer)

    def get_view(self, disabled=False):
        view = PomodoroView(self)

        if disabled:
            view.disable()

        return view

    async def switch_phase(self, timer: Timer, new_status_idx: int = None):
        if not new_status_idx:
            current_status_index = STATUS.index(timer.status)
            new_status_idx = (current_status_index + 1) % 2
        new_status = STATUS[new_status_idx]
        remaining = get_remaining(timer, new_status)
        timer.update(status=new_status, remaining=remaining).where(Timer.id == timer.id).execute()
        await self.edit_message(Timer.get(Timer.id == timer.id))
        await self.send_acoustic_notification(timer)

    async def edit_message(self, timer: Timer, mentions=None, create_new=True):
        channel = await self.bot.fetch_channel(timer.channel)
        message_id = timer.message
        try:
            message = await channel.fetch_message(message_id)
            embed = timer.create_embed()

            if create_new:
                await message.delete()
                view = self.get_view(disabled=timer.status == STATUS[-1])
                mentions = get_mentions(timer) if not mentions else mentions
                new_msg = await channel.send(mentions, embed=embed, view=view)
                timer.update(message=new_msg.id).where(Timer.id == timer.id).execute()
                message = new_msg
            else:
                await message.edit(embed=embed, view=self.get_view())
            return str(message.id)
        except discord.errors.NotFound:
            timer.update(status=STATUS[-1]).where(Timer.id == timer.id).execute()
            return None

    async def send_acoustic_notification(self, timer: Timer):
        guild = self.bot.get_guild(timer.guild)
        filename = get_soundfile(timer.status)
        voice_channels = await get_voice_channels(guild, list(timer.attendees))

        for id, voice_channel in voice_channels.items():
            await play_sound(voice_channel, filename)

        for vc in self.bot.voice_clients:
            await vc.disconnect()

    @tasks.loop(minutes=1)
    async def run_timer(self):
        for timer in Timer.select().where(Timer.status != STATUS[-1]):
            timer.update(remaining=timer.remaining - 1).where(Timer.id == timer.id).execute()
            if timer.remaining <= 1:
                await self.switch_phase(timer)
            else:
                await self.edit_message(timer, create_new=False)

    @run_timer.before_loop
    async def before_timer(self):
        await asyncio.sleep(60)


async def setup(bot: commands.Bot) -> None:
    pomodoro = Pomodoro(bot)
    await bot.add_cog(pomodoro)
    bot.add_view(PomodoroView(pomodoro))
