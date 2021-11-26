import os
import re
from datetime import datetime

import disnake
from dotenv import load_dotenv

load_dotenv()
DATE_TIME_FMT = os.getenv("DISCORD_DATE_TIME_FORMAT")


async def send_dm(user, message, embed=None):
    """ Send DM to a user/member """

    if type(user) is disnake.User or type(user) is disnake.Member:
        if user.dm_channel is None:
            await user.create_dm()

        await user.dm_channel.send(message, embed=embed)


def is_mod(ctx):
    author = ctx.author
    roles = author.roles

    for role in roles:
        if role.id in [int(os.getenv("DISCORD_MOD_ROLE")), int(os.getenv("DISCORD_ADMIN_ROLE"))]:
            return True

    return False


def is_valid_time(time):
    return re.match(r"^\d+[mhd]?$", time)


def to_minutes(time):
    if time[-1:] == "m":
        return int(time[:-1])
    elif time[-1:] == "h":
        h = int(time[:-1])
        return h * 60
    elif time[-1:] == "d":
        d = int(time[:-1])
        h = d * 24
        return h * 60

    return int(time)


def date_to_string(date: datetime):
    return date.strftime(DATE_TIME_FMT)


def date_from_string(date: str):
    return datetime.strptime(date, DATE_TIME_FMT)


async def files_from_attachments(attachments):
    files = []
    for attachment in attachments:
        files.append(await attachment.to_file(spoiler=attachment.is_spoiler()))

    return files
