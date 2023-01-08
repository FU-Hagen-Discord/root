import discord
from discord import app_commands, Interaction
from discord.ext import commands

from models import Topic, Link


@app_commands.guild_only()
class Links(commands.GroupCog, name="links", description="Linkverwaltung für Kanäle."):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="show", description="Zeige Links für diesen Kanal an.")
    @app_commands.describe(topic="Zeige nur Links für dieses Thema an.", public="Zeige die Linkliste für alle.")
    async def cmd_links(self, interaction: Interaction, topic: str = None, public: bool = False):
        await interaction.response.defer(ephemeral=not public)

        if not Topic.has_links(interaction.channel_id):
            await interaction.edit_original_response(content="Für diesen Channel sind noch keine Links hinterlegt.")
            return
        if topic and not Topic.has_links(interaction.channel_id, topic=topic):
            await interaction.edit_original_response(content=f"Für das Thema `{topic}` sind in diesem Channel keine "
                                                             f"Links hinterlegt. Versuch es noch mal mit einem anderen "
                                                             f"Thema, oder lass dir mit `/links show` alle Links in "
                                                             f"diesem Channel ausgeben")
            return

        embed = discord.Embed(title=f"Folgende Links sind in diesem Channel hinterlegt:\n")

        for topic in Topic.get_topics(interaction.channel_id, topic=topic):
            topic.append_field(embed)

        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="add", description="Füge einen neuen Link hinzu.")
    @app_commands.describe(topic="Thema, zu dem dieser Link hinzugefügt werden soll.",
                           link="Link, der hinzugefügt werden soll.", title="Titel des Links.")
    async def cmd_add_link(self, interaction: Interaction, topic: str, link: str, title: str):
        await interaction.response.defer(ephemeral=True)
        topic = topic.lower()
        topic_entity = Topic.get_or_create(channel=interaction.channel_id, name=topic)
        Link.create(link=link, title=title, topic=topic_entity[0].id)
        await interaction.edit_original_response(content="Link erfolgreich hinzugefügt.")

    @app_commands.command(name="remove-link", description="Einen Link entfernen.")
    @app_commands.describe(topic="Theme zu dem der zu entfernende Link gehört.",
                           title="Titel des zu entfernenden Links.")
    async def cmd_remove_link(self, interaction: Interaction, topic: str, title: str):
        await interaction.response.defer(ephemeral=True)
        topic = topic.lower()

        if not Topic.has_links(interaction.channel_id):
            await interaction.edit_original_response(content="Für diesen Channel sind noch keine Links hinterlegt.")
            return
        if topic_entity := Topic.get_or_none(Topic.channel == interaction.channel_id, Topic.name == topic):
            if link := Link.get_or_none(Link.title == title, Link.topic == topic_entity.id):
                link.delete_instance(recursive=True)
                await interaction.edit_original_response(content=f'Link {title} entfernt')
            else:
                await interaction.edit_original_response(content='Ich konnte den Link leider nicht finden.')
        else:
            await interaction.edit_original_response(content='Ich konnte das Thema leider nicht finden.')
            return

    @app_commands.command(name="remove-topic", description="Ein Thema mit allen zugehörigen Links entfernen.")
    @app_commands.describe(topic="Zu entfernendes Thema.")
    async def cmd_remove_topic(self, interaction: Interaction, topic: str):
        await interaction.response.defer(ephemeral=True)
        topic = topic.lower()

        if not Topic.has_links(interaction.channel_id):
            await interaction.edit_original_response(content="Für diesen Channel sind noch keine Links hinterlegt.")
            return
        if topic_entity := Topic.get_or_none(Topic.channel == interaction.channel_id, Topic.name == topic):
            topic_entity.delete_instance(recursive=True)
            await interaction.edit_original_response(content=f'Thema {topic} mit allen zugehörigen Links entfernt')
        else:
            await interaction.edit_original_response(content='Ich konnte das Thema leider nicht finden.')
            return

    @app_commands.command(name="edit-link", description="Einen bestehenden Link in der Liste bearbeiten.")
    @app_commands.describe(topic="Thema zu dem der zu bearbeitende Link gehört.",
                           title="Titel des zu bearbeitenden Links.", new_title="Neuer Titel des Links.",
                           new_topic="Neues Thema des Links.", new_link="Neuer Link.")
    async def cmd_edit_link(self, interaction: Interaction, topic: str, title: str, new_title: str,
                            new_topic: str = None, new_link: str = None):
        await interaction.response.defer(ephemeral=True)
        topic = topic.lower()
        new_title = title if not new_title else new_title
        new_topic = topic if not new_topic else new_topic.lower()

        if not Topic.has_links(interaction.channel_id):
            await interaction.edit_original_response(content="Für diesen Channel sind noch keine Links hinterlegt.")
            return

        if topic_entity := Topic.get_or_none(Topic.channel == interaction.channel_id, Topic.name == topic):
            if link := Link.get_or_none(Link.title == title, Link.topic == topic_entity.id):
                new_link = link.link if not new_link else new_link
                new_topic_entity = Topic.get_or_create(channel=interaction.channel_id, name=new_topic)
                link.update(title=new_title, link=new_link, topic=new_topic_entity[0].id).where(
                    Link.id == link.id).execute()
                if len(list(topic_entity.links)) == 0:
                    topic_entity.delete_instance()
                await interaction.edit_original_response(content=f'Link {title} bearbeitet.')
            else:
                await interaction.edit_original_response(content='Ich konnte den Link leider nicht finden.')
        else:
            await interaction.edit_original_response(content='Ich konnte das Thema leider nicht finden.')

    @app_commands.command(name="edit-topic", description="Thema bearbeiten.")
    @app_commands.describe(topic="Zu bearbeitendes Thema", new_topic="Neues Thema")
    async def cmd_edit_topic(self, interaction: Interaction, topic: str, new_topic: str):
        await interaction.response.defer(ephemeral=True)
        topic = topic.lower()
        new_topic = new_topic.lower()

        if not Topic.has_links(interaction.channel_id):
            await interaction.edit_original_response(content="Für diesen Channel sind noch keine Links hinterlegt.")
            return

        if topic_entity := Topic.get_or_none(Topic.channel == interaction.channel_id, Topic.name == topic):
            topic_entity.update(name=new_topic).execute()
            await interaction.edit_original_response(content=f"Thema {topic} bearbeitet.")
        else:
            await interaction.edit_original_response(content='Ich konnte das Thema leider nicht finden.')


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Links(bot))
