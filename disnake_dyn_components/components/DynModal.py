from disnake.ui import Modal, TextInput


class DynModal(Modal):

    def __init__(self, *, title: str):
        super().__init__(title=title, components=[])


class DynTextInput(TextInput):

    def __init__(self, label: str, **kwargs):
        super().__init__(label=label, custom_id="", **kwargs)

    def to_text_input(self) -> TextInput:
        return TextInput(
            label=self.label, custom_id=self.custom_id,
            style=self.style, placeholder=self.placeholder,
            value=self.value, required=self.required,
            min_length=self.min_length, max_length=self.max_length
        )
