import disnake
from disnake.ext import commands
import logging
import os
import dotenv

from disnake_dyn_components import DynComponents


logging.basicConfig(level=logging.WARN)
log = logging.getLogger(__name__)

dotenv.load_dotenv()


class MyClient(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dyn_components = DynComponents(self)


bot = MyClient(intents=disnake.Intents.default())

bot.load_extensions("examples/example_cog")

bot.run(os.getenv("TOKEN"))
