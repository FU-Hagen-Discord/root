from aiohttp import ClientSession
from bs4 import BeautifulSoup
from discord.ext import commands, tasks

import models


class News(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config["extensions"][__name__.split(".")[-1]]
        self.url = self.config.get("url")
        self.channel_id = self.config.get("channel_id")
        self.news_role = self.config.get("news_role")
        self.announcement_text = self.config.get("announcement_text")
        self.news_loop.start()

    @tasks.loop(hours=1)
    async def news_loop(self):
        async with ClientSession() as session:
            async with session.get(self.url) as r:
                if r.status == 200:
                    content = await r.read()
                    soup = BeautifulSoup(content, "html.parser")
                    channel = await self.bot.fetch_channel(self.channel_id)

                    for news in soup.find("ul", attrs={"class": "fu-link-list"}).find_all("li"):
                        date = news.span.text
                        title = str(news.a.text)
                        link = news.a['href']

                        if link[0] == "/":
                            link = f"https://www.fernuni-hagen.de" + link

                        if news := models.News.get_or_none(link=link):
                            if news.date != date:
                                await self.announce_news(channel, date, title, link)
                                news.update(date=date).where(models.News.link == link).execute()
                        else:
                            await self.announce_news(channel, date, title, link)
                            models.News.create(link=link, date=date)

    async def announce_news(self, channel, date, title, link):
        await channel.send(
            self.announcement_text.replace("{news_role}", f"{self.news_role}").replace("{date}", f"{date}").replace(
                "{title}", f"{title}").replace("{link}", f"{link}"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(News(bot))
