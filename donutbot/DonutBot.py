from dataclasses import dataclass
import datetime
import os
import random
import pickle
from pathlib import Path
from typing import Optional, cast

import discord
import inflect
import pytz

from Logic import Logic, Source
from Data import Data
from OpenAIQuerier import OpenAIQuerier

@dataclass
class DonutData:
    autotop_message_id: int
    autotop_message_channel_id: int
    autotop_message_url: str

class DonutBot:
    discord_bot: discord.Bot
    logic: Logic
    openai: OpenAIQuerier
    pluralizer: inflect.engine
    persistent_data: Optional[DonutData]

    yeepees = ("Yum!!", "Yeepee!!", "Hurray!!", "Hurrah!!", "Yumsies!!", "Nom!!!", "Yaaay!!", "Tasty!", "Love it!!", "Awww yeah!", "Now That's What I Call Donut 1998.")
    sads = ("Oh no :(", "Poor donut, gone too soon :/", ":(", "So sad :(", "RIP bozo!!", "Gone but not forgotten.", "Goodbye donut I will never forget you :(")

    env_admin_name = "DONUT_ADMIN"
    top_style = "ALT" # Alt is better on mobile but the regular one is prettier on desktop. Pick your poison

    PERSISTENT_PATH = "/var/data/donuts/donuts_persist.dat"


    def __init__(self, discord_bot: discord.Bot) -> None:
        self.discord_bot = discord_bot
        self.logic = Logic(Data())
        self.openai = OpenAIQuerier()
        self.pluralizer = inflect.engine()
        self.persistent_data = None

        if Path(self.PERSISTENT_PATH).exists():
            with open(self.PERSISTENT_PATH, "rb") as f:
                self.persistent_data = pickle.load(f)


    async def on_message(self, message: discord.Message):
        if str(message.channel.id) == os.getenv("CHANNEL_ID") and len(message.attachments) > 0:
            for attachment in message.attachments:
                if attachment.content_type is not None and "image" in attachment.content_type and "!nobot" not in message.content:
                    donuts = self.openai.analyse_pic(attachment.url)

                    if donuts == 0:
                        await message.channel.send("Doesn't look like a donut to me!")
                    else:


                        if "!maybebot" in message.content:
                            await message.channel.send(f"That would have been {self.pluralizer.number_to_words(donuts)} {self.pluralizer.plural_noun("donut", donuts)}.")
                        else:
                            await message.channel.send(f"{random.choice(self.yeepees)} {self.pluralizer.number_to_words(donuts).capitalize()} {self.pluralizer.plural_noun("donut", donuts)} for {self.logic.normalize_name(message.author.name)}!") # type: ignore
                            self.logic.add(message.author.name, donuts, Source.AI)
                            await self.update_autotop()

    async def add(self, ctx: discord.ApplicationContext, number: int):
        self.logic.add(ctx.user.name, number, Source.MANUAL)
        await ctx.respond(f"{random.choice(self.yeepees)} {number} {self.pluralizer.plural_noun("point", number)} to {self.logic.normalize_name(ctx.user.name)}")
        await self.update_autotop()

    async def remove(self, ctx: discord.ApplicationContext, number: int):
        self.logic.remove(ctx.user.name, number, Source.MANUAL)
        await ctx.respond(f"{random.choice(self.sads)} -{number} {self.pluralizer.plural_noun("point", number)} to {self.logic.normalize_name(ctx.user.name)}")
        await self.update_autotop()

    async def adjust(self, ctx: discord.ApplicationContext, number: int, username: str):
        if ctx.user.name == os.getenv(self.env_admin_name):
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

        now = datetime.datetime.now()
        start_of_year = datetime.datetime(now.year, 1, 1)
        start_of_year_delta = now - start_of_year
        end_of_year = datetime.datetime(now.year, 12, 31)
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

                with open(self.PERSISTENT_PATH, "wb") as f:
                    pickle.dump(persistent_data, f)
        else:
            await ctx.respond(f"There's already an auto-updating leaderboard, it's here: {self.persistent_data.autotop_message_url}")

    async def update_autotop(self):
        if self.persistent_data is not None:
            channel = self.discord_bot.get_channel(self.persistent_data.autotop_message_channel_id)

            if channel:
                message = await channel.fetch_message(self.persistent_data.autotop_message_id) # type: ignore
                await message.edit(embed=self.get_leaderboard_embed(True))

    def get_leaderboard_embed(self, update_footer: bool) -> discord.Embed:
        results = self.logic.get_top()

        embed = discord.Embed(
            title="🍩 Donut Championship 2026 🍩",
            color=discord.Colour.gold(),
        )

        pos = 0
        last_score = -1
        tie = 1

        if self.top_style == "ALT":
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
            embed.set_footer(text=f"Last updated {datetime.datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M:%S")} PST")

        return embed
