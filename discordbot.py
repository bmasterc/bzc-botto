import sys

from core.main import DiscordBot, setup_min_log
from core.errorhandlercog import ErrorHandlerCog
from core.bzcpricecog import PriceCog
from core.utils import readJsonFile
from core.bzc_collection import BzcCollection

if __name__ == '__main__':
    setup_min_log()

    app_config = readJsonFile('data/app_config.json')

    # intents = discord.Intents.default()
    # intents.members = True

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        bzc_coll = BzcCollection()
        bzc_coll.rank_and_offers()
        floor = bzc_coll.get_floor_price('skeleton-kings')
        print(f"Floor: {floor}")
    else:
        bot = DiscordBot(
            command_prefix='!',
            # intents=intents
        )

        bot.add_cog(PriceCog(bot))
        bot.add_cog(ErrorHandlerCog(bot))

        if 'discord_key' in app_config and app_config['discord_key']:
            bot.run(app_config['discord_key'])
        else:
            raise Exception("Missing Discord Bot Key!")