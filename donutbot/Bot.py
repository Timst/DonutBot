import datetime
import os
import random

import discord
import inflect

from Logic import Logic, Source
from Data import Data
from OpenAIQuerier import OpenAIQuerier

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)
data = Data()
logic = Logic(data)
openai = OpenAIQuerier()
pluralizer = inflect.engine()

yeepees = ("Yum!!", "Yeepee!!", "Hurray!!", "Hurrah!!", "Yumsies!!", "Nom!!!", "Yaaay!!", "Tasty!", "Love it!!", "Awww yeah!", "Now That's What I Call Donut 1998.")
sads = ("Oh no :(", "Poor donut, gone too soon :/", ":(", "So sad :(", "RIP bozo!!", "Gone but not forgotten.", "Goodbye donut I will never forget you :(")

env_token_name = "DONUT_TOKEN"
env_admin_name = "DONUT_ADMIN"
top_style = "ALT" # Alt is better on mobile but the regular one is prettier on desktop. Pick your poison

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if str(message.channel.id) == os.getenv("CHANNEL_ID") and len(message.attachments) > 0:
        for attachment in message.attachments:
            if attachment.content_type is not None and "image" in attachment.content_type and "!nobot" not in message.content:
                donuts = openai.analyse_pic(attachment.url)

                if donuts == 0:
                    await message.channel.send("Doesn't look like a donut to me!")
                else:


                    if "!maybebot" in message.content:
                        await message.channel.send(f"That would have been {pluralizer.number_to_words(donuts)} {pluralizer.plural_noun("donut", donuts)}.")
                    else:
                        await message.channel.send(f"{pluralizer.number_to_words(donuts).capitalize()} {pluralizer.plural_noun("donut", donuts)} for {logic.normalize_name(message.author.name)}!") # type: ignore
                        logic.add(message.author.name, donuts, Source.AI)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready, let's get donuting!")

@bot.slash_command(name="add", description="Record one or more donuts")
@discord.option("number", type=discord.SlashCommandOptionType.integer)
async def add(ctx: discord.ApplicationContext, number: int):
    logic.add(ctx.user.name, number, Source.MANUAL)
    await ctx.respond(f"{random.choice(yeepees)} {number} {pluralizer.plural_noun("point", number)} to {logic.normalize_name(ctx.user.name)}")

@bot.slash_command(name="remove", description="Remove one or more donuts, if you (or the bot) messed up")
@discord.option("number", type=discord.SlashCommandOptionType.integer)
async def remove(ctx: discord.ApplicationContext, number: int):
    logic.remove(ctx.user.name, number, Source.MANUAL)
    await ctx.respond(f"{random.choice(sads)} -{number} {pluralizer.plural_noun("point", number)} to {logic.normalize_name(ctx.user.name)}")

@bot.slash_command(name="adjust", description="(Admin only) Add or remove donuts from a person")
@discord.option("number", type=discord.SlashCommandOptionType.integer)
async def adjust(ctx: discord.ApplicationContext, number: int, username: str):
    if ctx.user.name == os.getenv(env_admin_name):
        if number > 0:
            logic.add(username, number, Source.ADMIN)
            await ctx.respond(f"Added {number} {pluralizer.plural_noun("point", number)} to {logic.normalize_name(username)}. Congratulations")
        else:
            number = -number
            logic.remove(username, number, Source.ADMIN)
            await ctx.respond(f"Removed {number} {pluralizer.plural_noun("point", number)} from {logic.normalize_name(username)}. Suck to suck")
    else:
        await ctx.respond("Nuh uh uh ☝️")

@bot.slash_command(name="stats", description="Get some helpful notes about your performance in the contest so far")
async def stats(ctx: discord.ApplicationContext):
    donuts = logic.get_score(logic.normalize_name(ctx.user.name))
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

        await ctx.respond(f"""So far this year you've eaten **{donuts}** {pluralizer.plural_noun("donut", donuts)}, at a rate of {rate} donuts per day.\n
That's a total of {calories} calories!\n
If you continue on this trend, by the end of the year you will have eaten **{projection}** {pluralizer.plural_noun("donut", donuts)}.
Or {projection_calories} calories. That's probably fine.""")

@bot.slash_command(name="top", description="Get the current leaderboard")
async def top(ctx: discord.ApplicationContext):
    results = logic.get_top()

    embed = discord.Embed(
        title="🍩 Donut Championship 2026 🍩",
        color=discord.Colour.gold(),
    )

    pos = 1

    if top_style == "ALT":
        results_str = ""

        for name, score in results.items():
            results_str += f"{"# " if pos == 1 else "## " if pos == 2 else "### " if pos == 3 else "**" if pos == 4 else ""}{pos} – {name} ({score} {pluralizer.plural_noun("pt", score)}){"**" if pos == 4 else ""}\n"
            pos +=1

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

    await ctx.respond("Good job everybody!!", embed=embed)

bot.run(os.getenv(env_token_name))
