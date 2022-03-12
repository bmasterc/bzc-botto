from asyncore import read
import discord

import core.main as dbot, os, json
from core.bzc_collection import BzcCollection
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

class PriceCog(discord.ext.commands.Cog, name='BZC Price Cog'):
    def __init__(self, bot):
        self.bot:dbot.DiscordBot = bot

        self.bzc_coll = BzcCollection()

    @discord.ext.commands.command(name="floor")
    async def floor(self, ctx: commands.Context):

        if "skel" in str(ctx.message):
            ret = self.bzc_coll.get_floor_price("skeleton-kings")
        else:
            ret = "What the #$#%@ did you just say??"

        await ctx.send(ret)


    # @discord.ext.commands.Cog.listener()
    # async def on_member_join(self, member):
    #     channel = member.guild.system_channel
    #     if channel is not None:
    #         await channel.send(f'A wild {member.mention} has appeared!')

    @discord.ext.commands.command(name="8ball")
    async def magic_8(self, ctx: commands.Context):
        import random
        await ctx.message.channel.send('😺𝐻𝑒𝓁𝓁𝑜😺')

        responses = [
            "It is certain",
            "Without a doubt",
            "You may rely on it",
            "Yes definitely",
            "It is decidedly so",
            "As I see it, yes",
            "Most likely",
            "Yes",
            "Outlook good",
            "Signs point to yes",
            "Reply hazy try again",
            "Better not tell you now",
            "Ask again later",
            "Cannot predict now",
            "Concentrate and ask again",
            "Don't count on it",
            "Outlook not so good",
            "My sources say no",
            "Very doubtful",
            "My reply is no"
        ]

        ret = None
        while not ret:
            if "meaning of life" in str(ctx.message):
                ret = "The Magic 8 Ball says: 42"
            else:
                answer = random.choice(responses)
                ret = f"The Magic 8 Ball says: {answer}"

        await ctx.send(ret)

    def chart_trending_stocktwits_vol(self, days=5, top=6):
        trending_url = f'https://api.stocktwits.com/api/2/trending/symbols.json'
        expire = None

        try:
            trending_symbols = self.sess.get_url_retry(trending_url, cache_expire=expire)

            import pandas as pd
            import matplotlib.pyplot as plt
            plt.style.use('dark_background')
            fig, ax = plt.subplots()

            for i in range(min(len(trending_symbols['symbols']), top)):
                row = trending_symbols['symbols'][i]
                twitvol_url = f'https://api.stocktwits.com/api/2/symbols/{row["symbol"]}/volume.json'

                volume = self.sess.get_url_retry(twitvol_url, cache_expire=expire)

                vols = []

                for vol_row in volume['data'][:days]:
                    vols.append({'day': vol_row['timestamp'][-2:], row["symbol"]:vol_row['volume_score']})

                df = pd.DataFrame(reversed(vols))

                df.plot(x='day', y=row["symbol"], ax=ax)

            fig.suptitle('Current Trending StockTwitter Volume', fontsize=12)
            fig.set_size_inches(5, 4)

            fig.savefig('data/trend.png') # , dpi=100

            return discord.File('data/trend.png')

            import io
            buf = io.BytesIO()
            fig.savefig(buf, dpi=100)
            buf.seek(0)

            return discord.File(buf)
        except Exception as e:
            self.log(e)
