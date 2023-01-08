import io

import discord
from discord.ext import commands


class ModMail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config["extensions"][__name__.split(".")[-1]]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if type(message.channel) is discord.DMChannel:
            channel = await self.bot.fetch_channel(self.config["channel_id"])
            files = []

            for attachment in message.attachments:
                fp = io.BytesIO()
                await attachment.save(fp)
                files.append(discord.File(fp, filename=attachment.filename))

            await channel.send(f"Nachricht von <@!{message.author.id}>:")
            await channel.send(message.content, files=files)
            await message.channel.send("Danke, deine Nachricht wurde an das Admin-/Mod-Team weitergeleitet.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModMail(bot))
