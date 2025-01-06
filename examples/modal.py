import disnake
from disnake.ext import commands
import logging
import os
import dotenv
import datetime

from disnake_dyn_components import DynComponents, DynTextInput


logging.basicConfig(level=logging.WARN)
log = logging.getLogger(__name__)

dotenv.load_dotenv()

bot = commands.Bot(intents=disnake.Intents.default())


# Create a components store to search for collisions between them
components = DynComponents(bot)


# Modals models
@components.create_modal(
    "mute_user",
    "Mute user",
    {
        "duration": DynTextInput("Duration (minutes)"),
        "reason": DynTextInput("Reason", style=disnake.TextInputStyle.long)
    }
)
async def mute_user_modal(inter: disnake.ModalInteraction, text_values, user_id: int):
    text_duration = text_values["duration"]
    try:
        duration = float(text_duration)
    except ValueError:
        return await inter.send("Duration must be number")

    member = inter.guild.get_member(user_id) or await inter.guild.fetch_member(user_id)
    await member.timeout(duration=duration * 60, reason=text_values["reason"])

    await inter.send(
        f"Member <@{user_id}> was muted",
        allowed_mentions=disnake.AllowedMentions.none()
    )


@components.create_modal(
    "rename_user",
    "Rename",
    {
        "name": DynTextInput("New Name"),
        "reason": DynTextInput("Reason", style=disnake.TextInputStyle.long)
    }
)
async def rename_user_modal(inter: disnake.ModalInteraction, text_values, user_id: int):
    new_name = text_values["name"]

    member = inter.guild.get_member(user_id) or await inter.guild.fetch_member(user_id)
    await member.edit(nick=new_name, reason=text_values["reason"])

    await inter.send(
        f"Member <@{user_id}> was renamed",
        allowed_mentions=disnake.AllowedMentions.none()
    )


# Buttons models
@components.create_button("mute_user", label="Mute", style=disnake.ButtonStyle.primary)
async def mute_user_button(inter: disnake.MessageInteraction, user_id: int):
    if inter.message.interaction_metadata.user.id != inter.author.id:
        return await inter.response.send_message("Unavailable")
    await inter.response.send_modal(mute_user_modal(user_id))


@components.create_button("rename_user", label="Rename", style=disnake.ButtonStyle.green)
async def rename_user_button(inter: disnake.MessageInteraction, user_id: int):
    if inter.message.interaction_metadata.user.id != inter.author.id:
        return await inter.response.send_message("Unavailable")
    await inter.response.send_modal(rename_user_modal(user_id))


@bot.slash_command()
@commands.has_permissions(moderate_members=True)
async def mod_profile(inter: disnake.AppCmdInter, member: disnake.Member):
    embed = (disnake.Embed(title="Example Member profile", timestamp=datetime.datetime.now(datetime.UTC))
             .set_thumbnail(member.display_avatar.url)
             .set_author(name=bot.user.display_name, icon_url=bot.user.display_avatar.url)
             .set_footer(text=f"Status: {member.status}\nActivity: {member.activity}\n"))

    await inter.send(
        embed=embed,
        components=[
            # We create buttons by passing the parameters specified in the model
            rename_user_button(member.id),
            mute_user_button(member.id)
        ]
    )


bot.run(os.getenv("TOKEN"))
