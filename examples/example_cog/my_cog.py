import random

from disnake.ext.commands import Cog, slash_command
from disnake import MessageInteraction, AppCmdInter
from disnake_dyn_components.dyncomponents import DynComponents
from examples.cog_test import MyClient


class MyCog(Cog):

    components = DynComponents()  # no args or None

    @staticmethod
    @components.create_button("random", label="random!")
    async def random_number(inter: MessageInteraction, a: int, b: int):
        await inter.send(f"You random number: {random.randint(a, b)}")

    def __init__(self, bot: MyClient):
        self.bot = bot
        self.bot.dyn_components.merge(self.components)  # add cog components to bot

    @slash_command()
    async def create_random(self, inter: AppCmdInter, a: int, b: int):
        await inter.send("Generate number [a, b]", components=[self.random_number(a, b)])


def setup(bot):
    bot.add_cog(MyCog(bot))
