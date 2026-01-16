import os
import random

import discord
import inflect

from Logic import Logic
from Data import Data
from OpenAIQuerier import OpenAIQuerier

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)
data = Data()
logic = Logic(data)
openai = OpenAIQuerier()

yeepees = ("YUM", "YEEPEE", "HURRAY", "HURRAH", "YUMSIES", "NOM", "YAAAY", "TASTY", "LOVE IT")

token_name = "DONUT_TOKEN"

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
                    p = inflect.engine()

                    if "!maybebot" in message.content:
                        await message.channel.send(f"That would have been {p.number_to_words(donuts)} {p.plural_noun("donut", donuts)}.") # type: ignore
                    else:
                        await message.channel.send(f"{p.number_to_words(donuts).capitalize()} {p.plural_noun("donut", donuts)} for {logic.normalize_name(message.author.name)}!") # type: ignore
                        logic.add(message.author.name, donuts)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready, let's get donuting!")

@bot.slash_command(name="add", description="Record one or more donuts")
@discord.option("number", type=discord.SlashCommandOptionType.integer)
async def add(ctx: discord.ApplicationContext, number: int):
    logic.add(ctx.user.name, number)
    await ctx.respond(random.choice(yeepees))

@bot.slash_command(name="remove", description="Remove one or more donuts, if you (or the bot) messed up")
@discord.option("number", type=discord.SlashCommandOptionType.integer)
async def remove(ctx: discord.ApplicationContext, number: int):
    logic.remove(ctx.user.name, number)
    await ctx.respond("OH NO")

@bot.slash_command(name="top", description="Get the current leaderboard")
async def top(ctx: discord.ApplicationContext):
    results = logic.get_top()

    embed = discord.Embed(
        title="🍩 Donut Championship 2026 🍩",
        color=discord.Colour.blurple(),
    )

    pos = 1
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


bot.run(os.getenv(token_name))
