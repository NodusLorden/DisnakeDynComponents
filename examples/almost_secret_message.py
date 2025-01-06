import disnake
from disnake.ext import commands
import logging
import os
import dotenv

from disnake_dyn_components import DynComponents


logging.basicConfig(level=logging.WARN)
log = logging.getLogger(__name__)

dotenv.load_dotenv()

bot = commands.Bot(intents=disnake.Intents.default())


components = DynComponents(bot)


# """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
# Do not use this example to transmit really secret data!!!
# The custom_id of the button comes to the user's client and will be visible to him if desired
# """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


def message_button_separator(custom_id: str, sep=":") -> list[str]:
    """
    | ident | user_id (hex) |         message        |
    |  hello:78d5128db82000b:Entering text!!! :) Woo |
            ^ split         ^ split           ^ not split
    """
    return custom_id.split(sep, 2)[1:]


def message_button_collector(ident: str, button_data: list[str], sep=":") -> str:
    """
    Ignore the check for the presence of a separator in the arguments,
    since we believe that there will be none in ident and user_id
    """
    return sep.join([ident] + button_data)


@components.create_button(
    "hello",
    label="Send",
    style=disnake.ButtonStyle.green,
    separator=message_button_separator,
    collector=message_button_collector
    # Need to override the separator because the user input may have a character to separate
)
async def message_button(inter: disnake.MessageInteraction, user_id: int, msg: str):
    # user_id is id of saved in button user
    if user_id == inter.author.id:
        await inter.send(f"Message for you:\n`{msg}`", ephemeral=True)
    else:
        await inter.send(f"This message is not addressed to you :(", ephemeral=True)


@bot.slash_command()
async def send_privet_message(
        inter: disnake.AppCmdInter,
        user: disnake.User,
        message: str = commands.Param(max_length=60)
):
    await inter.send(
        "Click to view secret message",
        components=[
            message_button(user.id, message)
        ]
    )


bot.run(os.getenv("TOKEN"))
