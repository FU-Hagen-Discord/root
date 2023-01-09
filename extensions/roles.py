import discord
from discord import app_commands, Interaction
from discord.ext import commands

from views.role_view import RoleView


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config["extensions"][__name__.split(".")[-1]]
        self.assignable_roles = self.config["assignable_roles"]
        self.channel_id = self.config["channel_id"]
        self.message_id = self.config.get("message_id")

    def get_key(self, role):
        """ Get the key for a given role. This role is used for adding or removing a role from a user. """

        for key, role_name in self.assignable_roles.items():
            if role_name == role.name:
                return key

    # @commands.command(name="stats")
    @app_commands.command(name="stats", description="Statistik zur Rollenzuweisung auf diesem Server.")
    @app_commands.describe(public="Zeige die Statistik öffentlich für alle sichtbar.")
    async def cmd_stats(self, interaction: Interaction, public: bool):
        """ Sends stats in Chat. """
        await interaction.response.defer(ephemeral=not public)

        roles = {}
        for role_category in self.assignable_roles.values():
            if role_category["in_stats"]:
                for role in role_category["roles"].values():
                    roles[role["name"]] = role

        embed = discord.Embed(title="Statistiken",
                              description=f'Wir haben aktuell {interaction.guild.member_count} Mitglieder auf diesem Server, verteilt auf folgende Rollen:')

        for role in interaction.guild.roles:
            if roles.get(role.name):
                embed.add_field(name=role.name, value=f'{len(role.members)} Mitglieder', inline=False)

        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="update-roles", description="Aktualisiere die Nachricht zur Rollenvergabe.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_roles=True)
    async def cmd_update_roles(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = await self.bot.fetch_channel(self.channel_id)
        message = await channel.fetch_message(self.message_id) if self.message_id else None
        view = RoleView(assignable_roles=self.assignable_roles)

        embed = discord.Embed(title="Such dir deine Rollen aus",
                              description="Durch Klicken auf den Button unter dieser Nachricht kannst du dir selbst "
                                          "einige Rollen vergeben.")

        if message:
            await message.edit(content="", embed=embed, view=view)
        else:
            await channel.send(embed=embed, view=view)
        await interaction.edit_original_response(content="Rollenvergabe aktualisiert.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roles(bot))
    bot.add_view(RoleView(assignable_roles=bot.config["extensions"][__name__.split(".")[-1]]["assignable_roles"]))
