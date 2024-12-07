import disnake
from disnake.ext import commands
import logging
import os
import dotenv

from disnake_dyn_components import DynButtons


logging.basicConfig(level=logging.WARN)
log = logging.getLogger(__name__)

dotenv.load_dotenv()

bot = commands.Bot(intents=disnake.Intents.default())


# Create a button store to search for collisions between them
buttons = DynButtons(bot)


# Create a button model
@buttons.create_button("hello", label="Send", style=disnake.ButtonStyle.blurple)
async def hello_button(inter: disnake.MessageInteraction, user_id: int):
    await inter.send(
        f"User {inter.author.mention} say hello <@{user_id}>",
        allowed_mentions=disnake.AllowedMentions.none()
    )


@bot.slash_command()
async def send_hello_buttons(inter: disnake.AppCmdInter, first_member: disnake.Member, second_member: disnake.Member):
    await inter.send(
        "Click for send Hello",
        components=[
            # We create buttons by passing the parameters specified in the model
            hello_button(first_member.id),
            hello_button(second_member.id)
        ]
    )


bot.run(os.getenv("TOKEN"))
