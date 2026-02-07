A lil Discord bot using [Pycord](https://pycord.dev/), sqlite and the openAI API to keep tabs on our donut championship. Mostly based on AI-based image recognition, with some additional features.

100% homemade garbage, no LLM involved (in the coding, that is), all the mistakes and suboptimal patterns are mine.


## What
This uses Pycord to process pictures sent to a specified channel. The pictures are forwarded to OpenAI, and if donut(s) are detected, a tally is incremented (and recorded to an sqlite DB). There are also slash commands to manually update the record and get the leaderboard.

## Config
You'll need to provide your own bot (see [pycord's doc](https://guide.pycord.dev/getting-started/creating-your-first-bot)), and then copy the `config.sample.toml` file to `/var/data/donuts/config.toml`, and change at least the following values:
- `bot_token`: discord bot token, as provided on the Discord dev dashboard
- `admin_username`: username (not display name! It's case-sensitive, too) of a user that will be able to use `/adjust`.
- `channel_id`: what channel to watch. See [this help article](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID#h_01HRSTXPS5FMK2A5SMVSX4JW4E) to get a channel ID.
- `api_key`: your OpenAI API key, as provided on the OpenAI dev dashboard

In addition, the system uses these files. Their paths can be configured in the config file:
- `/var/data/donuts/donuts.db`: the database file. If it doesn't exist, it will be created on first run. Only a single table ("Records") with ID, user, count, operation (add or remove) and timestamp.
- `/var/data/donuts/names.json`: (optional) a key-value file to match discord username to real name. If not provided, or if a username is not in it, the username will be used instead.
- `/var/data/donuts/donuts_persist.dat`: automatically created file to save a reference to `/autotop`'s message

## How
Start the bot with [Poetry](https://python-poetry.org/) by running `poetry run python donutbot/Main.py`.

Once running, it will watch for the specific channel ID of any server your bot is in (if you're running this across different servers, you'll need different instances). When pictures have been posted, it sends them to OpenAI for donut adjudication, and update the tally accordingly.

If you just want to see how a picture would be processed, write `!maybebot` and it will evaluate the image without changing the scores. If you don't want Sam Altman to see your donut pics, write `!nobot` and it won't process them at all.

If you ate a donut but forgot to take a photo (how convenient!), you can use the slash command `/add [number]` to add an arbitrary number of donuts to your score. Inversely if the bot messed up (or you did), you can use `/remove [number]`. If you're the admin (see config above), you can also use `/adjust [number] [username]`, where number can be negative or positive, to add/remove points from a user (use their discord account name, not display name).

Then to get the tally at any time, use `/top`. To get a tally that automagically updates itself every time the score changes, use `/autotop` instead. You can also show that as a time chart with `/chart`. That one takes a project parameter: use `/chart False` to get the scores so far, and `/chart True` to get a trendline to the end of the year.

To make yourself sad, use `/stats`.

If the picture system is enabled in the config file, a small (800x800 by default, configurable) version of valid donut pics is saved in `/var/data/donuts/pics`, with a subfolder per user. You can then run `/collage` to get a neat collage of all the donuts you've eaten! Wee! You can also look at other people's collage with `/audit`, if you don't trust their numbers. Finally, you can print a picture of every donut ever posted with `/board`. If you're limited on memory size (the full 80MP picture allowed by discord will eat about 600MiB of memory), you can set a lower resolution in the `max_board_size` setting of the config file.

If you're running this on a channel that already has pictures, you (the admin) can use `/ingest` to process all the existing pictures. Note that this does respect !nobot and !maybebot directives (these pictures won't get archived), but it does not check pictures against the AI again, so any kind of picture could be saved.