from asyncore import read
import discord

import core.main as dbot, os, json
from core.bzc_collection import BzcCollection
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ToDo
# -BZC Tip Bot
# -Floor Prices
# -Ranking Per Wallet
# -Trait price alerts

rpc_url = 'https://polygon-rpc.com'
abi_url = 'https://api.polygonscan.com/api?module=contract&action=getabi&address='

scheduler = AsyncIOScheduler()
collections = {"skeleton-kings": {
                'quantity': 1000,
                'contract': '0xfc92a46f38b5a347ab5ea2e764390ac8bb4057f6',
                'metadata_type': 'generative'
                },"billionairezombiesclub": {
                'quantity': 10000,
                'contract': '0x4bca2c2ece9402b5d4dd031b49d48166c40b7957',
                'metadata_type': 'generative'
                },"bzc-metaverse": {
                'quantity': 10000,
                'contract': '0x99ca9a688eece77dad66e0378b67bc8a0f2d7eef',
                'metadata_type': 'item'
                },"bzc-skeleton-keys": {
                'quantity': 1000,
                'contract': '0xee5d848c6d5bf44681610154f733da2ea3e37cf6',
                'metadata_type': 'single'
                },"bzc-metacrystals": {
                'quantity': 10000,
                'contract': '0x578945b61c97f6c4e3371dc215ec866f170ff9cc',
                'metadata_type': 'single'
                },"bzc-skeleton-keys-3d": {
                'quantity': 1000,
                'contract': '0xa6b0eef8c87fb1544689b05d22e3fd55e4fe369b',
                'metadata_type': 'single'
                }}

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
