import discord


class RoleView(discord.ui.View):
    def __init__(self, assignable_roles):
        super().__init__(timeout=None)
        self.assignable_roles = assignable_roles

    @discord.ui.button(label='Rollen auswählen', style=discord.ButtonStyle.green, custom_id='role_view:select')
    async def vote(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"Wähle zunächst eine Kategorie von Rollen aus. Anschließend kannst du dir innerhalb dieser Kategorie "
            f"Rollen zuweisen, oder entfernen.\n\n*(Nach Auswahl der Rollen kannst du diese Nachricht verwerfen. "
            f"Wenn die Rollenauswahl nicht funktioniert, bitte verwirf die Nachricht und Klicke erneut auf den Button "
            f"über dieser Nachricht.)*", view=RoleSelectionView(self.assignable_roles, interaction.user),
            ephemeral=True)


class RoleSelectionView(discord.ui.View):
    def __init__(self, assignable_roles, user, category=None):
        super().__init__(timeout=None)
        self.add_item(RoleCategoryDropdown(assignable_roles, category=category))
        if category:
            self.add_item(RoleSelectionDropdown(assignable_roles, user, category))


class RoleCategoryDropdown(discord.ui.Select):
    def __init__(self, assignable_roles, category=None):
        self.assignable_roles = assignable_roles
        options = [discord.SelectOption(label=role_category["name"], value=key, default=(category == key)) for
                   key, role_category in assignable_roles.items()]

        super().__init__(placeholder='Wähle eine Kategorie...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        await interaction.edit_original_response(
            view=RoleSelectionView(self.assignable_roles, interaction.user, category=self.values[0]))


def has_role(role, user):
    for r in user.roles:
        if r.name == role["name"]:
            return True
    return False


class RoleSelectionDropdown(discord.ui.Select):
    def __init__(self, assignable_roles, user, category):
        self.assignable_roles = assignable_roles
        self.user = user
        self.category = category
        options = [
            discord.SelectOption(label=role["name"], emoji=role.get("emoji"), value=key, default=has_role(role, user))
            for
            key, role in assignable_roles[category]["roles"].items()]

        super().__init__(placeholder='Wähle deine Rolle(n)....', min_values=0, max_values=len(options), options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        guild_roles = {role.name: role for role in interaction.guild.roles}
        member_roles = {role.name: role for role in interaction.user.roles}
        new_roles = []
        deprecated_roles = []
        for key, role in self.assignable_roles[self.category]["roles"].items():
            if key in self.values:
                if not member_roles.get(role["name"]):
                    if new_role := guild_roles.get(role["name"]):
                        new_roles.append(new_role)
            else:
                if member_role := member_roles.get(role["name"]):
                    deprecated_roles.append(member_role)

        [await interaction.user.add_roles(role) for role in new_roles]
        [await interaction.user.remove_roles(role) for role in deprecated_roles]

        reply = ""
        if len(new_roles) > 0:
            reply += f"Rollen {', '.join([f'`{role.name}`' for role in new_roles])} hinzugefügt!\n"
        if len(deprecated_roles) > 0:
            reply += f"Rollen {', '.join([f'`{role.name}`' for role in deprecated_roles])} entfernt!"
        if len(reply) > 0:
            await interaction.followup.send(reply, ephemeral=True)
