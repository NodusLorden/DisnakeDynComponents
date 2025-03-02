# Disnake dynamic components

Library for simplified creation of buttons for Discord bots created using disnake.

- [x] Button support
- [x] Modal support
- [x] Select menu support


## Fast start

`pip install disnake-dyn-components`

```python
import disnake
from disnake.ext import commands
from disnake_dyn_components import DynComponents
import dotenv
import os

dotenv.load_dotenv()

bot = commands.Bot(intents=disnake.Intents.default())

components = DynComponents(bot)


@components.create_button("say_hello", label="Hello")
async def hello_button(inter: disnake.MessageInteraction):
    await inter.send("Hello")


@bot.slash_command()
async def say_hello_buttons(inter: disnake.AppCmdInter):
    await inter.send(
        "Click for say hello",
        components=[hello_button()]
    )


bot.run(os.getenv("TOKEN"))
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

```python
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


@components.create_button(
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

# Examples
## Button Pagination this shared file

```python
import disnake
from disnake.ext import commands
import os
import dotenv
import io

from disnake_dyn_components import DynComponents


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
```

![img.png](images/button_send_file_img.png)

![img.png](images/button_page_1_img.png)

![img_1.png](images/button_page_2_img.png)

## Moder Profile this Modal

```python
import disnake
from disnake.ext import commands
import os
import dotenv
import datetime

from disnake_dyn_components import DynComponents, DynTextInput


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
```

![img.png](images/mod_profile_img.png)

![img.png](images/rename_modal_img.png)

![img.png](images/mute_modal_img.png)

![img.png](images/mute_img.png)

## Select Menu

```python
import disnake
from disnake.ext import commands
import logging
import os
import dotenv
import datetime
from disnake.ext.commands import Param

from disnake_dyn_components import DynComponents, DynTextInput, DynMenu


dotenv.load_dotenv()

bot = commands.Bot(intents=disnake.Intents.default())


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
```

![img.png](images/select_menu_message_img.png)

![img.png](images/choose_message_img.png)

![img.png](images/select_result_img.png)

### More [examples](https://github.com/NodusLorden/DisnakeDynComponents/tree/master/examples) here.

## Security

Transferring important but not confidential data via `custom_id` components is safe. 
Discord, for its part, checks the validity of components, including checking for `custom_id` matches,
which is why you can safely transfer role ids via buttons for subsequent issuance by the bot,
since when simulating pressing a non-existent button with a template `custom_id` with a replaced role,
Discord will block such a request and it will not reach the bot client.