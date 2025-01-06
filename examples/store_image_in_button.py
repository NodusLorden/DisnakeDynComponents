import disnake
from disnake.ext import commands
import logging
import os
import dotenv
import io
from PIL import Image

from disnake_dyn_components import DynComponents, Convertor


logging.basicConfig(level=logging.WARN)
log = logging.getLogger(__name__)

dotenv.load_dotenv()

bot = commands.Bot(intents=disnake.Intents.default())


with open("example\\char_table.txt", mode="r", encoding="utf-8") as file:
    chars = file.read()


class PILImage(Convertor):

    @staticmethod
    def from_string(string: str) -> Image.Image:
        image = Image.new(mode="RGBA", size=(18, 18))
        pixels = image.load()

        for i, char in enumerate(string):
            chunk = f"{chars.index(char):016b}"

            pos = i * 4
            c1 = int(chunk[0:4], 2) << 4 - 1
            c2 = int(chunk[4:8], 2) << 4 - 1
            c3 = int(chunk[8:12], 2) << 4 - 1
            c4 = int(chunk[12:16], 2) << 4 - 1

            pixels[(pos + 0) % image.width, (pos + 0) // image.width] = (c1, c1, c1, 255)
            pixels[(pos + 1) % image.width, (pos + 1) // image.width] = (c2, c2, c2, 255)
            pixels[(pos + 2) % image.width, (pos + 2) // image.width] = (c3, c3, c3, 255)
            pixels[(pos + 3) % image.width, (pos + 3) // image.width] = (c4, c4, c4, 255)

        return image.resize((180, 180))

    @staticmethod
    def to_string(value: Image.Image) -> str:
        string = ""
        chunk = ""
        image = value.resize((18, 18))
        pixels = image.load()
        for y in range(image.height):
            for x in range(image.width):
                chunk += f"{sum(pixels[x, y]) // 3 >> 4:04b}"
                if len(chunk) == 16:
                    string += chars[int(chunk, 2)]
                    chunk = ""
        return string


# Create a components store to search for collisions between them
components = DynComponents(bot)


# Create a button model
@components.create_button("send_image", label="Send", style=disnake.ButtonStyle.blurple)
async def image_button(inter: disnake.MessageInteraction, image: PILImage):
    image_buff = io.BytesIO()
    image.save(fp=image_buff, format="png")
    image_buff.seek(0)
    await inter.send(f"Image:", file=disnake.File(fp=image_buff, filename="image.png"))


@bot.slash_command()
async def send(inter: disnake.AppCmdInter, attachment: disnake.Attachment):
    image_buff = io.BytesIO()
    if attachment.content_type not in ('image/png', 'image/jpg', 'image/jpeg'):
        await inter.send("No image in message")
        return

    await attachment.save(fp=image_buff, seek_begin=True)

    image = Image.open(image_buff)

    await inter.send(
        "Send Image",
        components=[
            image_button(image)
        ]
    )


bot.run(os.getenv("TOKEN"))
