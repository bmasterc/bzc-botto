from core.main import DiscordBot, setup_min_log
from core.errorhandlercog import ErrorHandlerCog
from core.bzcpricecog import PriceCog
from core.utils import readJsonFile

if __name__ == '__main__':
    setup_min_log()

    app_config = readJsonFile('data/app_config.json')

    # intents = discord.Intents.default()
    # intents.members = True

    bot = DiscordBot(
        command_prefix='!', 
        # intents=intents
    )

    bot.add_cog(PriceCog(bot))
    bot.add_cog(ErrorHandlerCog(bot))

    bot.run(app_config['discord_key'])