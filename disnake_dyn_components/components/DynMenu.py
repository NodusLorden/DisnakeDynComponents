import disnake
from disnake import User, Role, Member, ChannelType
from typing import Optional, Union, Sequence

from disnake.abc import Messageable


class _DynMenu:

    def __init__(
            self,
            menu_type: disnake.ComponentType,
            options: list[str],
            channel_types: Optional[Sequence[ChannelType]],
            default_values: Optional[Sequence[Union[Messageable]]],
            placeholder: Optional[str],
            min_values: int,
            max_values: int,
            disabled: bool,
    ):
        self.menu_type: disnake.ComponentType = menu_type
        self.options: list[str] = options
        self.channel_types: Optional[Sequence[ChannelType]] = channel_types
        self.default_values: Optional[Sequence[Messageable]] = default_values
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled


class DynMenuFabric:

    @staticmethod
    def string_select(
            options: list[str],
            placeholder=None,
            min_values=1,
            max_values=1,
            disabled=False
    ):
        return _DynMenu(
            menu_type=disnake.ComponentType.string_select,
            options=options,
            channel_types=None,
            default_values=None,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
        )

    @staticmethod
    def user_select(
            default_values: Optional[Sequence[User]] = None,
            placeholder=None,
            min_values=1,
            max_values=1,
            disabled=False
    ):
        return _DynMenu(
            menu_type=disnake.ComponentType.user_select,
            options=[],
            channel_types=None,
            default_values=default_values,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
        )

    @staticmethod
    def role_select(
            default_values: Optional[Sequence[Role]] = None,
            placeholder=None,
            min_values=1,
            max_values=1,
            disabled=False
    ):
        return _DynMenu(
            menu_type=disnake.ComponentType.role_select,
            options=[],
            channel_types=None,
            default_values=default_values,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
        )

    @staticmethod
    def mentionable_select(
            default_values: Optional[Sequence[Union[User, Member, Role]]] = None,
            placeholder=None,
            min_values=1,
            max_values=1,
            disabled=False
    ):
        return _DynMenu(
            menu_type=disnake.ComponentType.mentionable_select,
            options=[],
            channel_types=None,
            default_values=default_values,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
        )

    @staticmethod
    def channel_select(
            channel_types: Optional[Sequence[ChannelType]] = None,
            default_values: Optional[Sequence[Messageable]] = None,
            placeholder=None,
            min_values=1,
            max_values=1,
            disabled=False
    ):
        return _DynMenu(
            menu_type=disnake.ComponentType.channel_select,
            options=[],
            channel_types=channel_types,
            default_values=default_values,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
        )


DynMenu = DynMenuFabric()
