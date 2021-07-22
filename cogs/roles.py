import json
import os

import discord
import emoji
from discord.ext import commands

import utils
from cogs.help import help, handle_error, help_category


@help_category("updater", "Updater",
               "Diese Kommandos werden zum Updaten von Nachrichten benutzt, die Boty automatisch erzeugt.")
@help_category("info", "Informationen", "Kleine Helferlein, um schnell an Informationen zu kommen.")
class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.roles_file = os.getenv("DISCORD_ROLES_FILE")
        self.channel_id = int(os.getenv("DISCORD_ROLE_CHANNEL"))
        self.role_message_id = int(os.getenv("DISCORD_ROLE_MSG", "0"))
        self.assignable_roles = {}
        self.load_roles()

    def load_roles(self):
        """ Loads all assignable roles from ROLES_FILE """

        roles_file = open(self.roles_file, mode='r')
        self.assignable_roles = json.load(roles_file)

    def get_key(self, role):
        """ Get the key for a given role. This role is used for adding or removing a role from a user. """

        for key, role_name in self.assignable_roles.items():
            if role_name == role.name:
                return key

    @help(
        category="info",
        brief="Gibt die Mitgliederstatistik aus."
    )
    @commands.command(name="stats")
    async def cmd_stats(self, ctx):
        """ Sends stats in Chat. """

        guild = ctx.guild
        members = await guild.fetch_members().flatten()
        answer = f''
        embed = discord.Embed(title="Statistiken",
                              description=f'Wir haben aktuell {len(members)} Mitglieder auf diesem Server, verteilt auf folgende Rollen:')

        for role in guild.roles:
            if not self.get_key(role):
                continue
            role_members = role.members
            if len(role_members) > 0 and not role.name.startswith("Farbe"):
                embed.add_field(name=role.name, value=f'{len(role_members)} Mitglieder', inline=False)

        no_role = 0
        for member in members:
            # ToDo Search for study roles only!
            if len(member.roles) == 1:
                no_role += 1

        embed.add_field(name="\u200B", value="\u200b", inline=False)
        embed.add_field(name="Mitglieder ohne Rolle", value=str(no_role), inline=False)

        await ctx.channel.send(answer, embed=embed)

    @help(
        category="updater",
        brief="Aktualisiert die Vergabe-Nachricht von Studiengangs-Rollen.",
        mod=True
    )
    @commands.command("update-roles")
    @commands.check(utils.is_mod)
    async def cmd_update_degree_program(self, ctx):
        channel = await self.bot.fetch_channel(self.channel_id)
        message = None if self.role_message_id == 0 else await channel.fetch_message(self.role_message_id)

        embed = discord.Embed(title="Vergabe von Studiengangs-Rollen",
                              description="Durch klicken auf die entsprechende Reaktion kannst du dir die damit assoziierte Rolle zuweisen, oder entfernen. Dies funktioniert so, dass ein Klick auf die Reaktion die aktuelle Zuordnung dieser Rolle ändert. Das bedeutet, wenn du die Rolle, die mit :scales: assoziiert ist, schon hast, aber die Reaktion noch nicht ausgewählt hast, dann wird dir bei einem Klick auf die Reaktion diese Rolle wieder weggenommen. ")

        value = f""
        for role_emoji, name in self.assignable_roles.items():
            if emoji.EMOJI_ALIAS_UNICODE_ENGLISH.get(role_emoji):
                value += f"{role_emoji} : {name}\n"
            else:
                value += f"<{role_emoji}> : {name}\n"

        embed.add_field(name="Rollen",
                        value=value,
                        inline=False)

        if message:
            await message.edit(content="", embed=embed)
            await message.clear_reactions()
        else:
            message = await channel.send(embed=embed)

        for key in self.assignable_roles.keys():
            if role_emoji := emoji.EMOJI_ALIAS_UNICODE_ENGLISH.get(key):
                await message.add_reaction(role_emoji)
            else:
                await message.add_reaction(f"<{key}>")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id or payload.message_id != self.role_message_id:
            return

        role_emoji = emoji.UNICODE_EMOJI_ALIAS_ENGLISH.get(payload.emoji.name)

        if not role_emoji:
            role_emoji = str(payload.emoji)[1:-1]
        if role_emoji not in self.assignable_roles:
            return

        role_name = self.assignable_roles.get(role_emoji)
        guild = await self.bot.fetch_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        roles = member.roles

        await message.remove_reaction(payload.emoji, member)

        for role in roles:
            if role.name == role_name:
                await member.remove_roles(role)
                await utils.send_dm(member, f"Rolle \"{role.name}\" erfolgreich entfernt")
                break
        else:
            guild_roles = guild.roles

            for role in guild_roles:
                if role.name == role_name:
                    await member.add_roles(role)
                    await utils.send_dm(member, f"Rolle \"{role.name}\" erfolgreich hinzugefügt")

    async def cog_command_error(self, ctx, error):
        await handle_error(ctx, error)
