from discord import Member


def is_mod(user: Member, bot):
    for mod_role in bot.config["mod_roles"]:
        if user.get_role(mod_role):
            return True

    return False
