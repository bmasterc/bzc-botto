
import os, sys
from discord.ext import commands

import logging
# logging.getLogger('matplotlib').propagate = False

class DiscordBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.log = logging.Logger(__name__)

        self.channels = {}

    async def on_ready(self):
        self.status = 'started'
        print('Logged on as {0}!'.format(self.user))
        for guild in self.guilds:
            self.log.info(
                f'{self.user} is connected to the following guild:\n'
                f'{guild.name}(id: {guild.id})')

            for channel in guild.channels:
                self.channels[f'{guild.name}_{channel.name}'] = channel

    # async def on_message(self, message):
    #     try:
    #         if message.author == self.user:
    #             return

    #     except Exception as e:
    #         self.log(e)

    # async def send_message(self, channel, message):
    #     try:
    #         if not self.is_closed():
    #             await self.channels[channel].send(message)
    #     except Exception as e:
    #         self.log(e)

    # async def save_channel(self, channel):
    #     try:
    #         messages = await self.channels[channel].history(limit=10).flatten()
    #         for msg in messages:
    #             print(msg.content)
    #     except Exception as e:
    #         self.log(e)


    # https://realpython.com/how-to-make-a-discord-bot-python/
    # async def on_member_join(member):
    #     await member.create_dm()
    #     await member.dm_channel.send(f'Hi {member.name}, welcome to Funneh Munneh!')

root_logger = logging.getLogger()
console_logger = logging.StreamHandler(sys.stdout)
def setup_min_log(file_logging_suffix=None):

    root_logger.setLevel(logging.INFO)

    console_logger.setLevel(logging.INFO)
    console_logger.setFormatter(logging.Formatter('{levelname}:{module}.{funcName}() {asctime}: {message}', style='{'))
    root_logger.addHandler(console_logger)

    if file_logging_suffix:
        from logging.handlers import TimedRotatingFileHandler
        if not os.path.isdir('data/logs'):
            os.makedirs('data/logs')
        logging.Logger.log_path = os.path.realpath(f'data/logs/bzcpricebot{file_logging_suffix}.log')
        print(f'Setting Log Output to Log File "{logging.Logger.log_path}", line 0')
        fh = TimedRotatingFileHandler(logging.Logger.log_path, when='midnight', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('{name}:{module}.{funcName}() {asctime} {levelname}: {message}', style='{'))
        root_logger.addHandler(fh)