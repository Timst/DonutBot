from dataclasses import dataclass
from datetime import datetime
import random
import pickle
from pathlib import Path
from typing import Optional, cast

import discord
import inflect
import pytz

from Config import config
from Logic import Logic, Source
from Data import Data
from OpenAIQuerier import OpenAIQuerier
from PicArchive import PicArchive

@dataclass
class DonutData:
    autotop_message_id: int
    autotop_message_channel_id: int
    autotop_message_url: str

class DonutBot:
    discord_bot: discord.Bot
    pics: PicArchive
    logic: Logic
    openai: OpenAIQuerier
    pluralizer: inflect.engine
    persistent_data: Optional[DonutData]

    def __init__(self, discord_bot: discord.Bot, pics: PicArchive) -> None:
        self.discord_bot = discord_bot
        self.pics = pics

        self.logic = Logic(Data())
        self.openai = OpenAIQuerier()
        self.pluralizer = inflect.engine()
        self.persistent_data = None

        if Path(config.settings["files"]["persistence"]).exists():
            with open(config.settings["files"]["persistence"], "rb") as f:
                self.persistent_data = pickle.load(f)

    async def on_message(self, message: discord.Message):
        if str(message.channel.id) == config.settings["discord"]["channel_id"] and len(message.attachments) > 0:
            for attachment in message.attachments:
                if attachment.content_type is not None and "image" in attachment.content_type and "!nobot" not in message.content:
                    donuts = self.openai.analyse_pic(attachment.url)

                    if donuts == 0:
                        await message.channel.send("Doesn't look like a donut to me!")
                    else:
                        if "!maybebot" in message.content:
                            await message.channel.send(f"That would have been {self.pluralizer.number_to_words(donuts)} {self.pluralizer.plural_noun("donut", donuts)}.")
                        else:
                            await message.channel.send(f"{random.choice(config.settings["messages"]["yeepees"])} {self.pluralizer.number_to_words(donuts).capitalize()} {self.pluralizer.plural_noun("donut", donuts)} for {self.logic.normalize_name(message.author.name)}!") # type: ignore
                            self.logic.add(message.author.name, donuts, Source.AI)
                            await self.update_autotop()

                            if self.pics is not None:
                                await self.pics.save(message.author.name, attachment.url, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

    async def add(self, ctx: discord.ApplicationContext, number: int):
        if abs(number) > 10:
            await ctx.respond("Come on man")
        else:
            self.logic.add(ctx.user.name, number, Source.MANUAL)
            await ctx.respond(f"{random.choice(config.settings["messages"]["yeepees"])} {number} {self.pluralizer.plural_noun("point", number)} to {self.logic.normalize_name(ctx.user.name)}")
            await self.update_autotop()

    async def remove(self, ctx: discord.ApplicationContext, number: int):
        if abs(number) > 10:
            await ctx.respond("I will not let you destroy all these precious donuts")
        else:
            self.logic.remove(ctx.user.name, number, Source.MANUAL)
            await ctx.respond(f"{random.choice(config.settings["messages"]["sads"])} -{number} {self.pluralizer.plural_noun("point", number)} to {self.logic.normalize_name(ctx.user.name)}")
            await self.update_autotop()

    async def adjust(self, ctx: discord.ApplicationContext, number: int, username: str):
        if ctx.user.name == config.settings["discord"]["admin_username"]:
            if number > 0:
                self.logic.add(username, number, Source.ADMIN)
                await ctx.respond(f"Added {number} {self.pluralizer.plural_noun("point", number)} to {self.logic.normalize_name(username)}. Congratulations")
                await self.update_autotop()
            else:
                number = -number
                self.logic.remove(username, number, Source.ADMIN)
                await ctx.respond(f"Removed {number} {self.pluralizer.plural_noun("point", number)} from {self.logic.normalize_name(username)}. Suck to suck")
                await self.update_autotop()
        else:
            await ctx.respond("Nuh uh uh ☝️")

    async def stats(self, ctx: discord.ApplicationContext):
        donuts = self.logic.get_score(self.logic.normalize_name(ctx.user.name))
        all_donuts = self.logic.get_top()
        total_donuts = sum(all_donuts.values())
        total_calories = total_donuts * 250
        percentage = round(donuts/total_donuts * 100)

        now = datetime.now()
        start_of_year = datetime(now.year, 1, 1)
        start_of_year_delta = now - start_of_year
        end_of_year = datetime(now.year, 12, 31)
        end_of_year_delta = end_of_year - now

        if donuts == 0:
            await ctx.respond(f"You haven't eaten a single donut yet. But don't worry, there are still {end_of_year_delta.days} days left in the year! You can do it!")
        else:
            rate = round(donuts / start_of_year_delta.days, 2)
            projection = int(rate * end_of_year_delta.days)
            calories = donuts * 250
            projection_calories = projection * 250

            await ctx.respond(f"""So far this year you've eaten **{donuts}** {self.pluralizer.plural_noun("donut", donuts)}, at a rate of {rate} donuts per day.

That's a total of {calories} calories!

As a whole, the server has eaten **{total_donuts}** {self.pluralizer.plural_noun("donut", donuts)}, for a total of {total_calories} calories, and you're responsible for {percentage}% of it.

If you continue on this trend, by the end of the year you will have eaten **{projection}** {self.pluralizer.plural_noun("donut", donuts)}. Or {projection_calories} calories. That's probably fine.""")

    async def top(self, ctx: discord.ApplicationContext):
        await ctx.respond("Good job everybody!!", embed=self.get_leaderboard_embed(False))

    async def autotop(self, ctx: discord.ApplicationContext):
        if self.persistent_data is None:
            await ctx.defer()
            interaction = await ctx.respond("Good job everybody!! This message will update every time the score changes.", embed=self.get_leaderboard_embed(True))
            message = cast(discord.WebhookMessage, interaction)
            if message is not None:
                persistent_data = DonutData(message.id, message.channel.id, message.jump_url)
                self.persistent_data = persistent_data

                with open(config.settings["files"]["persistence"], "wb") as f:
                    pickle.dump(persistent_data, f)
        else:
            await ctx.respond(f"There's already an auto-updating leaderboard, it's here: {self.persistent_data.autotop_message_url}")

    async def update_autotop(self):
        if self.persistent_data is not None:
            channel = self.discord_bot.get_channel(self.persistent_data.autotop_message_channel_id)

            if channel:
                message = await channel.fetch_message(self.persistent_data.autotop_message_id) # type: ignore
                await message.edit(embed=self.get_leaderboard_embed(True))

    async def collage(self, ctx: discord.ApplicationContext, username: str, is_self: bool):
        if self.pics is None:
            await ctx.respond("Image saving system not enabled!")
        else:
            await ctx.defer()
            image = self.pics.make_collage(username)

            if image is None:
                if is_self:
                    await ctx.respond("Can't make a collage without pics. Go eat a donut.")
                else:
                    await ctx.respond(f"I don't have any pictures for {self.logic.normalize_name(username)} :(")
            else:
                image.save("/tmp/donutcollage.webp")
                file = discord.File("/tmp/donutcollage.webp")
                await ctx.respond(file = file)

    async def ingest(self, ctx: discord.ApplicationContext):
        if ctx.user.name == config.settings["discord"]["admin_username"]:
            await ctx.defer()
            if isinstance(ctx.channel, discord.TextChannel):
                async for message in ctx.channel.history(limit=None, after=datetime(datetime.now().year, 1, 1)):
                    if (
                    "!nobot" not in message.content and
                    "!maybebot" not in message.content and
                    len(message.attachments) > 0 and
                    message.author != self.discord_bot.user
                    ):
                        for attachment in message.attachments:
                            await self.pics.save(message.author.name, attachment.url, message.created_at.strftime("%Y-%m-%d_%H-%M-%S"))

            await ctx.respond("All done :)")
        else:
            await ctx.respond("Please, my network budget, it's very sick")

    def get_leaderboard_embed(self, update_footer: bool) -> discord.Embed:
        results = self.logic.get_top()

        embed = discord.Embed(
            title=config.settings["messages"]["top_title"],
            color=discord.Colour.gold(),
        )

        pos = 0
        last_score = -1
        tie = 1

        if config.settings["ui"]["use_compact_top"]:
            results_str = ""

            for name, score in results.items():
                if last_score != score:
                    pos += tie
                    tie = 1
                else:
                    tie += 1

                results_str += f"{"# " if pos == 1 else "## " if pos == 2 else "### " if pos == 3 else "**" if pos == 4 else ""}{pos} – {name} ({score} {self.pluralizer.plural_noun("pt", score)}){"**" if pos == 4 else ""}\n"
                last_score = score

            embed.description = results_str
        else:
            position = ""
            name = ""
            score = ""

            for item in results:
                position += f"{pos}\n"
                pos += 1

                name += f"{item[0]}\n"
                score += f"{item[1]}\n"

            embed.add_field(name="Position", value=position, inline=True)
            embed.add_field(name="Name", value=name, inline=True)
            embed.add_field(name="Score", value=score, inline=True)

        if update_footer:
            embed.set_footer(text=f"Last updated {datetime.now(pytz.timezone(config.settings["ui"]["timezone"])).strftime("%Y-%m-%d %H:%M:%S")} PST")

        return embed
