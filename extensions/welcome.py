import random
import re

import discord
from discord import app_commands, Interaction
from discord.ext import commands


@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
class Welcome(commands.GroupCog, name="welcome", description="Neue Mitglieder Willkommen heißen."):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config["extensions"][__name__.split(".")[-1]]
        self.channel_id = self.config.get("channel_id")
        self.message_id = self.config.get("welcome_message")

    @app_commands.command(name="update", description="Allgemeine Willkommensnachricht aktualisieren.")
    @app_commands.default_permissions(manage_guild=True)
    async def cmd_update_welcome(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        if not self.channel_id:
            await interaction.edit_original_response(content="Diese Funktion steht hier nicht zur Verfügung")
            return
        channel = await self.bot.fetch_channel(self.channel_id)
        message = None if self.message_id == 0 else await channel.fetch_message(self.message_id)

        embed = discord.Embed(title=":rocket: __FernUni Föderation__ :rocket:",
                              description="Willkommen auf dem interdisziplinären Server von und für FernUni-Studierende! Hier können FernUni-Studierende aus allen Fachrichtungen in Austausch treten, Ideen austauschen und gemeinsam an Projekten arbeiten: viel Potenzial für gegenseitige Bereicherung!")

        embed.add_field(name=":sparkles: Entstehung",
                        value="Die Betreiber:innen der verschiedenen FernUni-Discordserver haben sich vernetzt, um zusammenzuarbeiten. Aus mehreren Richtungen wurde der Wunsch nach einer fachübergreifender Plattform geäußert und daraufhin ist dieser Föderationsserver entstanden!",
                        inline=False)

        embed.add_field(name=":robot: Server-Bot",
                        value=f"Ich bin root. Beim <#{self.config['botuebungsplatz_channel']}> kannst du meine verschiedenen Befehle ausprobieren. Wenn du dort `/` schreibst, werden dir meine Befehle als Vorschläge zur Autovervollständigung angezeigt, mitsamt jeweiliger Erklärung des Befehls.",
                        inline=False)

        embed.add_field(name=":placard: Rollen",
                        value=f"Du kannst dir eine Discord-Rolle bei <id:customize> aussuchen, die deine Fakultätszugehörigkeit widerspiegelt.",
                        inline=False)

        embed.add_field(name=":scroll: Regeln",
                        value="Verhalte dich respektvoll und versuche Rücksicht auf deine Mitmenschen zu nehmen. Außerdem sind - wie überall auf Discord - diese Community-Richtlinien zu beachten: <https://discord.com/guidelines>.",
                        inline=False)

        embed.add_field(name=":link: Einladungslink",
                        value=f"Mitstudierende kannst du mit folgendem Link einladen: {self.config['invite_link']}.",
                        inline=False)

        embed.add_field(name="\u200b",
                        value="Viel Vergnügen auf dem Server!",
                        inline=False)

        if message:
            await message.edit(content="", embed=embed)
        else:
            await channel.send(embed=embed)

        await interaction.edit_original_response(content="Willkommensnachricht erfolgreich aktualisiert!")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.config.get("dm_message"):
            if member.dm_channel is None:
                await member.create_dm()

            await member.dm_channel.send(self.replace_variables(self.config["dm_message"]))

        if self.config.get("greeting_messages") and self.config.get("greeting_on_join"):
            channel = await self.bot.fetch_channel(self.config["greeting_channel"])
            await channel.send(self.replace_variables(
                random.choice(self.config["greeting_messages"]).replace("{user_id}", f"{member.id}")))

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if self.config.get("greeting_messages") and self.config.get("greeting_after_verification"):
            if before.pending != after.pending and not after.pending:
                channel = await self.bot.fetch_channel(self.config["greeting_channel"])
                await channel.send(self.replace_variables(
                    random.choice(self.config["greeting_messages"]).replace("{user_id}", f"{before.id}")))

    def replace_variables(self, message: str) -> str:
        return re.sub(r"\{[a-z_]+}", self.repl, message)

    def repl(self, matchobj):
        return f"{self.config.get(matchobj.group(0)[1:-1])}"

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Welcome(bot))
