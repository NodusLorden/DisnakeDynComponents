# Disnake dynamic components

Library for simplified creation of buttons for Discord bots created using disnake.

- [x] Button support
- [ ] Modal support
- [ ] Select menu support


## Fast start

```py
import disnake
from disnake.ext import commands
from disnake_dyn_components import DynButtons
import dotenv


dotenv.load_dotenv()

bot = commands.Bot(intents=disnake.Intents.default())

buttons = DynButtons(bot)


@buttons.create_button("say_hello", label="Hello")
async def hello_button(inter: disnake.MessageInteraction):
    await inter.send("Hello")


@bot.slash_command()
async def say_hello_buttons(inter: disnake.AppCmdInter):
    await inter.send(
        "Click for say hello",
        components=[hello_button()]
    )
```

## Work protocol

The library uses `ident` to determine the type of button pressed. The ident is placed in the `custom_id` of the button along with any data you choose to pass in.
> Important! The maximum length of custom_id is 100 characters, if this size is exceeded, you will receive an error

Since `ident` is used to determine whether a button is pressed, and it is found at the beginning, in order to avoid collisions, each `ident` should not be nested within another.

Example:

> `ident="Message"` and `ident="Message1"` - have a collision
> 
> `ident="Message1"` and `ident="Message2"` - do not have a collision

It is recommended to create all buttons at the beginning, rather than at runtime, since the `DynButtons` class automatically searches for collisions and raises an error if they are present.

Basically, ident and data are placed in a string with a `:` separator. If you need to change the transfer protocol, you can do this by passing functions for collecting and separating.

```py
def button_data_collector(ident: str, button_data: list[str], sep="#") -> str:
    if sep in ident:
        raise ValueError(
            f"The ident `{ident}` has the symbol `{sep}` in it,"
            f" which cannot be used because it is a separator"
        )
    for arg in button_data:
        if sep in arg:
            raise ValueError(
                f"The argument `{arg}` has the symbol `{sep}` in it,"
                f" which cannot be used because it is a separator"
            )
    return sep.join([ident] + button_data)


def button_data_separator(custom_id: str, sep="#") -> list[str]:
    # The first argument needs to be removed because it is ident
    return custom_id.split(sep)[1:]


@buttons.create_button(
    "hello",
    label="Send",
    separator=button_data_separator,
    collector=button_data_collector
)
async def message_button(inter: disnake.MessageInteraction, msg: str = ":)"):
    await inter.send(msg)
```

### Data

When you specify a parameter annotation, it is used to convert data from a string. You can create your own class that will handle type conversion from value to string and back. To make things easier, there is an abstract class `Convertor`.

Additionally, support for types is implemented:
- `int` convert to hex to save space
- `bool` convert to int, this values `0` and `1`
Types without annotations will implicitly try to convert to `string` and when returned, they will remain as that type.

## Example
### Pagination

```py
import disnake
from disnake.ext import commands
import logging
import os
import dotenv
import io

from disnake_dyn_components import DynButtons


logging.basicConfig(level=logging.WARN)
log = logging.getLogger(__name__)

dotenv.load_dotenv()

bot = commands.Bot(intents=disnake.Intents.default())


buttons = DynButtons(bot)

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

    prev_button = get_previous_button(file_index, page_index - 1)
    # Disable button in first page
    if page_index == 0:
        prev_button.disabled = True

    next_button = get_next_button(file_index, page_index + 1)
    # Disable if this is the only page.
    if not file_buff.read(1):
        next_button.disabled = True
    file_buff.seek(1000 * page_index)

    return prev_button, next_button, text


@buttons.create_button("next", label=">")
async def get_next_button(inter: disnake.MessageInteraction, file_index: int, page_index: int):
    await inter.response.defer(with_message=False)
    prev_button, next_button, text = get_button_and_text(file_index, page_index)
    await inter.edit_original_message(
        f"```\n{text}\n```",
        components=[prev_button, next_button]
    )


@buttons.create_button("previous", label="<")
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
```

More [examples](https://github.com/NodusLorden/DisnakeDynComponents/tree/master/examples) here.