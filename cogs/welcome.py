import os

import disnake
from disnake.ext import commands

import utils
from cogs.help import help, handle_error


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = int(os.getenv("DISCORD_WELCOME_CHANNEL"))
        self.message_id = int(os.getenv("DISCORD_WELCOME_MSG", "0"))

    @help(
      category="updater",
      brief="aktualisiert die Willkommensnachricht.",
      mod=True
      )
    @commands.command("update-welcome")
    @commands.check(utils.is_mod)
    async def cmd_update_welcome(self, ctx):
        channel = await self.bot.fetch_channel(self.channel_id)
        message = None if self.message_id == 0 else await channel.fetch_message(self.message_id)

        embed = disnake.Embed(title=":rocket: __FernUni Föderation__ :rocket:",
                              description="Willkommen auf dem interdisziplinären Server von und für FernUni-Studierende! Hier können FernUni-Studierende aus allen Fachrichtungen in Austausch treten, Ideen austauschen und gemeinsam an Projekten arbeiten: viel Potenzial für gegenseitige Bereicherung!")

        embed.add_field(name=":sparkles: Entstehung",
                        value="Die Betreiber:innen der verschiedenen FernUni-Discordserver haben sich vernetzt, um zusammenzuarbeiten. Aus mehreren Richtungen wurde der Wunsch nach einer fachübergreifender Plattform geäußert und daraufhin ist dieser Föderationsserver entstanden!",
                        inline=False)
        
        embed.add_field(name=":robot: Server-Bot",
                        value=f"Ich bin root. Beim <#{os.getenv('DISCORD_BOTUEBUNGSPLATZ_CHANNEL')}> kannst du meine verschiedenen Befehle ausprobieren. Wenn du dort `!help` schreibst, sende ich dir per Direktnachricht einen Überblick meiner Funktionen.",
                        inline=False)
        
        embed.add_field(name=":placard: Rollen",
                        value=f"Du kannst dir eine Discord-Rolle bei <#{os.getenv('DISCORD_ROLE_CHANNEL')}> aussuchen, die deine Fakultätszugehörigkeit widerspiegelt.",
                        inline=False)
        
        embed.add_field(name=":scroll: Regeln",
                        value="Verhalte dich respektvoll und versuche Rücksicht auf deine Mitmenschen zu nehmen. Außerdem sind - wie überall auf Discord - diese Community-Richtlinien zu beachten: <https://discord.com/guidelines>.",
                        inline=False)
        
        embed.add_field(name=":link: Einladungslink",
                        value=f"Mitstudierende kannst du mit folgendem Link einladen: {os.getenv('DISCORD_INVITE_LINK')}.",
                        inline=False)
        
        embed.add_field(name="\u200b",
                        value="Viel Vergnügen auf dem Server!",
                        inline=False)

        if message:
            await message.edit(content="", embed=embed)
        else:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await utils.send_dm(member,
                            f"Herzlich Willkommen bei der FernUni Föderation! Alle notwendigen Informationen, die du für den Einstieg brauchst, sowie die wenige Regeln, die aufgestellt sind, findest du in <#{self.channel_id}>\n"
                            f"Du darfst dir außerdem gerne im Channel <#{os.getenv('DISCORD_ROLE_CHANNEL')}> die passende Rolle zu deiner Fakultät zuweisen lassen. \n\n"
                            f"Falls du Fragen haben solltest, kannst du sie gerne bei der <#{os.getenv('DISCORD_OFFTOPIC_CHANNEL')}> stellen. Wenn du bei etwas Hilfe vom Moderationsteam brauchst, schreib mir doch eine private Nachricht, ich werde sie weiterleiten :writing_hand:.\n\n"
                            f"Viel Spaß beim erkunden des Servers und bis bald!")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.pending != after.pending and not after.pending:
            channel = await self.bot.fetch_channel(int(os.getenv("DISCORD_GREETING_CHANNEL")))
            await channel.send(f"Willkommen <@!{before.id}> im Kreise der FernUni-Studierenden :student:")

    async def cog_command_error(self, ctx, error):
        await handle_error(ctx, error)
