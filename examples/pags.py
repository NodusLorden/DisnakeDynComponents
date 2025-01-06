import disnake
from disnake.ext import commands
import logging
import os
import dotenv
import io

from disnake_dyn_components import DynComponents


logging.basicConfig(level=logging.WARN)
log = logging.getLogger(__name__)

dotenv.load_dotenv()

bot = commands.InteractionBot(intents=disnake.Intents.default())


components = DynComponents(bot)

files: list[io.BytesIO] = []


def get_button_and_text(file_index: int, page_index: int) -> tuple[disnake.ui.Button, disnake.ui.Button, str]:
    global files

    if len(files) <= file_index:
        prev_button = get_previous_button(file_index, page_index - 1)
        prev_button.disabled = True
        next_button = get_next_button(file_index, page_index + 1)
        next_button.disabled = True
        return prev_button, next_button, "The file no longer exists"

    file_buff = files[file_index]

    file_buff.seek(1000 * page_index)
    text = file_buff.read(1000).decode("utf-8")

    file_buff.seek(1000 * page_index)

    return (
        get_previous_button(file_index, page_index - 1).update(disabled=page_index == 0),
        get_next_button(file_index, page_index + 1).update(disabled=not file_buff.read(1)),
        text
    )


@components.create_button("next", label=">")
async def get_next_button(inter: disnake.MessageInteraction, file_index: int, page_index: int):
    await inter.response.defer(with_message=False)
    prev_button, next_button, text = get_button_and_text(file_index, page_index)
    await inter.edit_original_message(
        f"```\n{text}\n```",
        components=[prev_button, next_button]
    )


@components.create_button("previous", label="<")
async def get_previous_button(inter: disnake.MessageInteraction, file_index: int, page_index: int):
    await inter.response.defer(with_message=False)
    prev_button, next_button, text = get_button_and_text(file_index, page_index)
    await inter.edit_original_message(
        f"```\n{text}\n```",
        components=[prev_button, next_button]
    )


@bot.slash_command()
async def send_file(
        inter: disnake.AppCmdInter,
        file: disnake.Attachment
):
    global files
    await inter.response.defer(with_message=True)

    file_buff = io.BytesIO()
    await file.save(fp=file_buff, seek_begin=True)

    files.append(file_buff)
    file_index = len(files) - 1

    prev_button, next_button, text = get_button_and_text(file_index, 0)

    await inter.send(
        f"```\n{text}\n```",
        components=[prev_button, next_button]
    )


bot.run(os.getenv("TOKEN"))
