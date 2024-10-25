import json
from typing import Dict

import discord
from discord import Interaction, Message
from discord.ext import commands


class Root(commands.Bot):
    def __init__(self, *args, config: Dict, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config

    async def setup_hook(self) -> None:
        for extension, extension_config in self.config["extensions"].items():
            await self.load_extension(f"extensions.{extension}")

        await self.tree.sync()

    @staticmethod
    def dt_format():
        return "%d.%m.%Y %H:%M"


def load_config():
    fp = open("config.json", mode="r")
    return json.load(fp)


config = load_config()
bot = Root(command_prefix='!', help_command=None, activity=discord.Game(config["activity"]),
           intents=discord.Intents.all(), config=config)


@bot.tree.context_menu(name="📌 Nachricht anpinnen")
async def pin_message(interaction: Interaction, message: Message):
    await interaction.response.defer(ephemeral=True, thinking=True)
    await message.pin()
    await interaction.edit_original_response(content="Nachricht erfolgreich angepinnt!")


bot.run(config["token"])
