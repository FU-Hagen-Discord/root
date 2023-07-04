from aiohttp import ClientSession
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
import models


class Sprachrohr(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config["extensions"][__name__.split(".")[-1]]
        self.url = self.config.get("url")

        self.update_loop.start()

    @tasks.loop(hours=3)
    async def update_loop(self):
        async with ClientSession() as session:
            async with session.get(self.url) as r:
                if r.status == 200:
                    content = await r.read()
                    soup = BeautifulSoup(content, "html.parser")

                    for issue in soup.find("ul", attrs={"class": "wp-block-latest-posts__list"}).find_all("li"):
                        link = issue.find("a")
                        url = link["href"]
                        year = link.text[-4:]
                        issue_in_year = link.text[len("SprachRohr "):-5]

                        (sprach_rohr, created) = models.SprachRohr.get_or_create(url=url, year=year,
                                                                                 issue=issue_in_year)
                        if created:
                            await self.announce_new_issue(sprach_rohr)

    async def announce_new_issue(self, sprach_rohr: models.SprachRohr):
        if channel := await self.bot.fetch_channel(self.config.get("channel_id")):
            msg = await channel.send(f"{self.config.get('text')}\n{sprach_rohr.url}")
            if channel.is_news():
                await msg.publish()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Sprachrohr(bot))
