A lil Discord bot using [Pycord](https://pycord.dev/), sqlite and the openAI API to keep tabs on our donut championship. ~~Basically the simplest CRUD thing you could imagine.~~ Now with futuristic image processing!

100% homemade garbage, no LLM involved (in the coding, that is), all the mistakes and suboptimal patterns are mine.


## What

This uses Pycord to process pictures sent to a specified channel. The pictures are forwarded to OpenAI, and if donut(s) are detected, a tally is incremented (and recorded to an sqlite DB). There are also slash commands to manually update the record and get the leaderboard.

## Config

You'll need to provide your own bot (see [pycord's doc](https://guide.pycord.dev/getting-started/creating-your-first-bot)), and then have the following environment variables:
- `DONUT_TOKEN`: discord bot token, as provided on the Discord dev dashboard
- `DONUT_ADMIN`: username (not display name! It's case-sensitive, too) of a user that will be able to use /adjust.
- `CHANNEL_ID`: what channel to watch. See [this help article](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID#h_01HRSTXPS5FMK2A5SMVSX4JW4E) to get a channel ID.
- `OPENAI_API_KEY`: your OpenAI API key, as provided on the OpenAI dev dashboard

In addition, the system uses these files:
- `/var/data/donuts/donuts.db`: the database file. If it doesn't exist, it will be created on first run. Only a single table ("Records") with ID, user, count, operation (add or remove) and timestamp.
- `/var/data/donuts/names.json`: (optional) a key-value file to match discord username to real name. If not provided, or if a username is not in it, the username will be used instead.

## How
Once running, it will watch for the specific channel ID of any server the bot is in (yeah that's dumb. It's meant for one server, I didn't think this through too much). When pictures have been posted, it sends them to OpenAI for donut adjudication, and update the tally accordingly.

If you just want to see how a picture would be processed, write `!maybebot` and it will evaluate the image without changing the scores. If you don't want Sam Altman to see your donut pics, write `!nobot` and it won't process it at all.

If you ate donut but forgot to take a photo (how convenient!), you can use the slash command `/add [number]` to add an arbitrary number of donuts to your score. Inversely if the bot messed up (or you did), you can use `/remove [number]`. If you're the admin (see config above), you can also use `/adjust [number] [username]`, where number can be negative or positive, to add/remove points from a user (use their discord account name, not display name).

Then to get the tally at any time, use `/top`.
