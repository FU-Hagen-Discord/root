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
        channel = await self.bot.fetch_channel(self.channel_id)
        message = None if self.message_id == 0 else await channel.fetch_message(self.message_id)

        embed = discord.Embed(title=":rocket: __FernUni Föderation__ :rocket:",
                              description="Willkommen auf dem interdisziplinären Server von und für FernUni-Studierende! Hier können FernUni-Studierende aus allen Fachrichtungen in Austausch treten, Ideen austauschen und gemeinsam an Projekten arbeiten: viel Potenzial für gegenseitige Bereicherung!")

        embed.add_field(name=":sparkles: Entstehung",
                        value="Die Betreiber:innen der verschiedenen FernUni-Discordserver haben sich vernetzt, um zusammenzuarbeiten. Aus mehreren Richtungen wurde der Wunsch nach einer fachübergreifender Plattform geäußert und daraufhin ist dieser Föderationsserver entstanden!",
                        inline=False)

        embed.add_field(name=":robot: Server-Bot",
                        value=f"Ich bin root. Beim <#{self.config['botuebungsplatz_channel']}> kannst du meine verschiedenen Befehle ausprobieren. Wenn du dort `!help` schreibst, sende ich dir per Direktnachricht einen Überblick meiner Funktionen.",
                        inline=False)

        embed.add_field(name=":placard: Rollen",
                        value=f"Du kannst dir eine Discord-Rolle bei <#{self.config['role_channel']}> aussuchen, die deine Fakultätszugehörigkeit widerspiegelt.",
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
        if member.dm_channel is None:
            await member.create_dm()

        await member.dm_channel.send(f"Herzlich Willkommen bei der FernUni Föderation! Alle notwendigen Informationen, "
                                     f"die du für den Einstieg brauchst, sowie die wenige Regeln, die aufgestellt "
                                     f"sind, findest du in <#{self.channel_id}>\n"
                                     f"Du darfst dir außerdem gerne im Channel <#{self.config['role_channel']}> "
                                     f"die passende Rolle zu deiner Fakultät zuweisen lassen. \n\n"
                                     f"Falls du Fragen haben solltest, kannst du sie gerne bei der "
                                     f"<#{self.config['offtopic_channel']}> stellen. Wenn du bei etwas Hilfe vom "
                                     f"Moderationsteam brauchst, schreib mir doch eine private Nachricht, ich werde "
                                     f"sie weiterleiten :writing_hand:.\n\n"
                                     f"Viel Spaß beim erkunden des Servers und bis bald!")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.pending != after.pending and not after.pending:
            channel = await self.bot.fetch_channel(self.config["greeting_channel"])
            await channel.send(f"Willkommen <@!{before.id}> im Kreise der FernUni-Studierenden :student:")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Welcome(bot))
