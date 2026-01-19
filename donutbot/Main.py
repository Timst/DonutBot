import os

import discord

from DonutBot import DonutBot

intents = discord.Intents.default()
intents.message_content = True
discord_bot = discord.Bot(intents=intents)
donut_bot = DonutBot(discord_bot)

env_token_name = "DONUT_TOKEN"

@discord_bot.event
async def on_message(message: discord.Message):
    if message.author == discord_bot.user:
        return

    await donut_bot.on_message(message)

@discord_bot.event
async def on_ready():
    print(f"{discord_bot.user} is ready, let's get donuting!")

@discord_bot.slash_command(name="add", description="Record one or more donuts")
@discord.option("number", type=discord.SlashCommandOptionType.integer)
async def add(ctx: discord.ApplicationContext, number: int):
    await donut_bot.add(ctx, number)

@discord_bot.slash_command(name="remove", description="Remove one or more donuts, if you (or the bot) messed up")
@discord.option("number", type=discord.SlashCommandOptionType.integer)
async def remove(ctx: discord.ApplicationContext, number: int):
    await donut_bot.remove(ctx, number)

@discord_bot.slash_command(name="adjust", description="(Admin only) Add or remove donuts from a person")
@discord.option("number", type=discord.SlashCommandOptionType.integer)
async def adjust(ctx: discord.ApplicationContext, number: int, username: str):
    await donut_bot.adjust(ctx, number, username)

@discord_bot.slash_command(name="stats", description="Get some helpful notes about your performance in the contest so far")
async def stats(ctx: discord.ApplicationContext):
    await donut_bot.stats(ctx)

@discord_bot.slash_command(name="top", description="Get the current leaderboard")
async def top(ctx: discord.ApplicationContext):
    await donut_bot.top(ctx)

@discord_bot.slash_command(name="autotop", description="Post an auto-updating message with the leaderboard")
async def autotop(ctx: discord.ApplicationContext):
    await donut_bot.autotop(ctx)

discord_bot.run(os.getenv(env_token_name))
