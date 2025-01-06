import disnake
from disnake.ext import commands
import logging
import os
import dotenv
import datetime

from disnake.ext.commands import Param

from disnake_dyn_components import DynComponents, DynTextInput, DynMenu


logging.basicConfig(level=logging.WARN)
log = logging.getLogger(__name__)

dotenv.load_dotenv()

bot = commands.Bot(intents=disnake.Intents.default(), test_guilds=[832270428093284352])


# Create a components store to search for collisions between them
components = DynComponents(bot)


@components.create_select_menu(
    "send_message",
    DynMenu.user_select(placeholder="Choose User for send message"),
    separator=lambda x: x.split(":", 1)[1:]  # for ignore : in user messages
)
async def select_member_menu(inter: disnake.MessageInteraction, values, msg: str):
    await inter.response.defer(with_message=False)
    await inter.send(f"Message for {values[0].mention}: {msg}")


@bot.slash_command()
@commands.guild_only()
async def select_member(inter: disnake.AppCmdInter, msg: str = Param(max_length=50)):
    await inter.response.send_message(
        "Select member",
        components=[
            select_member_menu(msg)
        ]
    )


bot.run(os.getenv("TOKEN"))
