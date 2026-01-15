import os
import random
import discord
import dotenv
from Logic import Logic
from Data import Data

dotenv.load_dotenv()
bot = discord.Bot()
data = Data()
logic = Logic(data)

yeepees = ("YUM", "YEEPEE", "HURRAY", "HURRAH", "YUMSIES", "NOM", "YAAAY", "TASTY", "LOVE IT")

@bot.event
async def on_ready():
    print(f"{bot.user} is ready, let's get donuting!")

@bot.slash_command(name="add", description="Record one or more donuts")
@discord.option("number", type=discord.SlashCommandOptionType.integer) 
async def add(ctx: discord.ApplicationContext, number: int):
    logic.add(ctx.user.name, number)
    await ctx.respond(random.choice(yeepees))

@bot.slash_command(name="remove", description="Remove one or more donuts, if you messed up")
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

bot.run(os.getenv('TOKEN'))
