from discord import app_commands, Interaction
from discord.app_commands import Choice
from discord.ext import commands


@app_commands.guild_only()
class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="voice", description="Sprachkanäle öffnen oder schließen")
    @app_commands.describe(state="Wähle, ob die Sprachkanäle geöffnet oder geschlossen werden sollen.")
    @app_commands.choices(state=[Choice(name="open", value="open"), Choice(name="close", value="close")])
    @app_commands.default_permissions(manage_permissions=True)
    async def cmd_voice(self, interaction: Interaction, state: Choice[str]):
        await interaction.response.defer(ephemeral=True)
        voice_channels = interaction.guild.voice_channels
        if state.value == "open":
            for voice_channel in voice_channels:
                await voice_channel.edit(user_limit=0)
        elif state.value == "close":
            for voice_channel in voice_channels:
                await voice_channel.edit(user_limit=1)
        await interaction.edit_original_response(content="Status der Voice Channel erfolgreich geändert.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Welcome(bot))
