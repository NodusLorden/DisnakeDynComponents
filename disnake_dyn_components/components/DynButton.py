from disnake.ui import Button
from disnake import ButtonStyle, Emoji, PartialEmoji
from typing import Optional, Union, Self
from disnake import utils


class DynButton(Button):

    def update(
            self,
            style: ButtonStyle = utils.MISSING,
            label: str = utils.MISSING,
            disabled: bool = utils.MISSING,
            emoji: Optional[Union[str, Emoji, PartialEmoji]] = utils.MISSING,
            row: Optional[int] = utils.MISSING
    ) -> Self:
        if style is not utils.MISSING:
            self.style = style
        if label is not utils.MISSING:
            self.label = label
        if disabled is not utils.MISSING:
            self.disabled = disabled
        if emoji is not utils.MISSING:
            self.emoji = emoji
        if row is not utils.MISSING:
            self.row = row
        return self

    def to_button(self) -> Button:
        return Button(
            style=self.style, label=self.label, disabled=self.disabled,
            emoji=self.emoji, row=self.row, custom_id=self.custom_id
        )
