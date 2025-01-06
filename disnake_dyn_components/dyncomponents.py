import disnake.ui
from discord.ui.select import BaseSelect
from disnake.ext.commands.common_bot_base import CommonBotBase
from disnake import ButtonStyle, Emoji, PartialEmoji
from disnake.interactions.message import MessageInteraction
from disnake.interactions.modal import ModalInteraction
from disnake.ui import Button, TextInput, StringSelect, UserSelect, RoleSelect, MentionableSelect, ChannelSelect
from typing import Optional, Union, Callable, Concatenate, ParamSpec, Any
import logging
import inspect
from inspect import Signature, Parameter

from .components.DynButton import DynButton
from .components.DynModal import DynModal
from .components.DynModal import DynTextInput
from .components.DynMenu import _DynMenu
from .abc_convertor import Convertor


__all__ = ["DynComponents", "DynTextInput", "_DynMenu"]


log = logging.getLogger(__name__)


P = ParamSpec("P")


class DynComponents:

    def __init__(self, bot: CommonBotBase):
        self.__bot = bot
        self.__buttons_ident_list: list[str] = []  # button ident list for find collisions
        self.__modal_ident_list: list[str] = []  # modal ident list for find collisions
        self.__select_menu_ident_list: list[str] = []  # select menu ident list for find collisions

    def _add_button_ident(self, ident: str):
        self.__buttons_ident_list.append(ident)

    def _delete_button_ident(self, ident: str):
        self.__buttons_ident_list.remove(ident)

    def _get_button_ident_collision(self, ident: str) -> Optional[str]:
        """
        :return: string identifier with which the collision was found, otherwise None
        """
        for register_ident in self.__buttons_ident_list:
            if register_ident.startswith(ident) or ident.startswith(register_ident):
                return register_ident
        return None

    def _add_modal_ident(self, ident: str):
        self.__modal_ident_list.append(ident)

    def _delete_modal_ident(self, ident: str):
        self.__modal_ident_list.remove(ident)

    def _get_modal_ident_collision(self, ident: str) -> Optional[str]:
        """
        :return: string identifier with which the collision was found, otherwise None
        """
        for register_ident in self.__modal_ident_list:
            if register_ident.startswith(ident) or ident.startswith(register_ident):
                return register_ident
        return None

    def _add_select_menu_ident(self, ident: str):
        self.__select_menu_ident_list.append(ident)

    def _delete_select_menu_ident(self, ident: str):
        self.__select_menu_ident_list.remove(ident)

    def _get_select_menu_ident_collision(self, ident: str) -> Optional[str]:
        """
        :return: string identifier with which the collision was found, otherwise None
        """
        for register_ident in self.__select_menu_ident_list:
            if register_ident.startswith(ident) or ident.startswith(register_ident):
                return register_ident
        return None

    @staticmethod
    def _args_type_checker(sign: Signature, casted_kwargs):

        params: dict[str, Parameter] = dict(sign.parameters.items())
        required_params: dict[str, Parameter] = (
            dict(filter(lambda x: x[1].default is Signature.empty, params.items())))
        optional_params: dict[str, Parameter] = (
            dict(filter(lambda x: x[1].default is not Signature.empty, params.items())))

        if diff := set(casted_kwargs) - set(required_params) - set(optional_params):
            raise ValueError(f"Function has no parameters `{', '.join(diff)}`")

        if diff := set(required_params.keys()) - set(casted_kwargs.keys()):
            raise ValueError(f"Required arguments `{', '.join(diff)}` were not passed")

        # kwargs types check
        for param_name, value in casted_kwargs.items():
            param = params.get(param_name)
            if param is None:
                raise TypeError(f"Component builder does not have key word argument `{param_name}`")
            elif param.annotation is Signature.empty:
                log.warning(f"Dynamic Component parameter `{param_name}` has not type and will be casting to string")
            elif issubclass(param.annotation, Convertor):
                ...
            elif not isinstance(value, (param.annotation, Convertor)):
                raise TypeError(
                    f"Component builder expects argument `{param_name}`"
                    f" of type {param.annotation} but gets {type(param_name)}")

    @staticmethod
    def base_collector(ident: str, button_data: list[str], sep=":") -> str:
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

    @staticmethod
    def base_separator(custom_id: str, sep=":") -> list[str]:
        return custom_id.split(sep)[1:]

    @staticmethod
    def _convert_kwargs_to_strings_and_sort(
            sign: Signature,
            casted_kwargs: dict[str, Any]
    ) -> list[str]:
        """
        Convert kwargs to string and sort by signature order
        """
        # add optional params
        optional_default_params = dict(map(lambda x: (x.name, x.default), sign.parameters.values()))
        casted_kwargs.update(
            dict(filter(lambda x: x[0] not in casted_kwargs, optional_default_params.items()))
        )

        button_data = []
        for param_name, param in sign.parameters.items():
            val = casted_kwargs[param_name]
            annotation_type = param.annotation
            if annotation_type is int:
                button_data.append(hex(val)[2:])
            elif annotation_type is bool:
                button_data.append(str(int(val)))
            elif annotation_type is Signature.empty:
                button_data.append(str(val))
            elif issubclass(annotation_type, Convertor):
                button_data.append(annotation_type.to_string(val))
            else:
                button_data.append(str(val))

        return button_data

    @staticmethod
    def _convert_kwargs_from_strings(
            sign: Signature,
            button_data: list[str]
    ) -> dict[str, Any]:
        casted_kwargs: dict[str, Any] = {}
        for (param_name, param), val in zip(sign.parameters.items(), button_data):

            annotation_type = param.annotation
            if annotation_type is int:
                casted_kwargs[param_name] = int(val, 16)
            elif annotation_type is bool:
                casted_kwargs[param_name] = bool(int(val))
            elif annotation_type is Signature.empty:
                casted_kwargs[param_name] = val
            elif issubclass(annotation_type, Convertor):
                casted_kwargs[param_name] = annotation_type.from_string(val)
            else:
                casted_kwargs[param_name] = annotation_type(val)

        return casted_kwargs

    def create_button(
            self,
            ident: str,
            *,
            label: str,
            style: ButtonStyle = ButtonStyle.secondary,
            disabled: bool = False,
            emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
            row: Optional[int] = None,
            collector: Callable[[str, list[str]], str] = base_collector,
            separator: Callable[[str], list[str]] = base_separator
    ) -> Callable[[Callable[Concatenate[MessageInteraction, P], Any]], Callable[P, DynButton]]:
        collision = self._get_button_ident_collision(ident)
        if collision is not None:
            raise ValueError(f"Ident of button `{ident}` has collision this `{collision}`")

        if style is ButtonStyle.url or style is ButtonStyle.link:
            raise ValueError("Dyn buttons do not support url or link style")

        def builder(
                func: Callable[Concatenate[MessageInteraction, P], Any]
        ) -> Callable[P, DynButton]:

            _original_sign = inspect.signature(func)

            if not _original_sign.parameters:
                raise TypeError(
                    f"Invalid function structure, argument {MessageInteraction} is required in first position")

            _first_param, *_other_params = _original_sign.parameters.values()
            if _first_param.annotation not in (MessageInteraction, Signature.empty):
                raise TypeError(
                    f"Invalid first argument annotation,"
                    f" it should not be there or its type should be {MessageInteraction}")

            sign = _original_sign.replace(parameters=_other_params)

            async def check_dyn_button(inter: MessageInteraction):
                custom_id: str = inter.component.custom_id  # type: ignore
                if not custom_id.startswith(ident):
                    return
                custom_id_data = separator(custom_id)
                casted_kwargs = self._convert_kwargs_from_strings(sign, custom_id_data)
                await func(inter, **casted_kwargs)  # type: ignore

            def wrapper(*args: P.args, **kwargs: P.kwargs) -> DynButton:
                # args to kwargs
                casted_kwargs = dict(zip(sign.parameters.keys(), args))
                casted_kwargs.update(kwargs)
                self._args_type_checker(sign, casted_kwargs)

                button = DynButton(style=style, label=label, disabled=disabled, emoji=emoji, row=row)
                custom_id_data = self._convert_kwargs_to_strings_and_sort(sign, casted_kwargs)
                custom_id = collector(ident, custom_id_data)
                if not custom_id.startswith(ident):
                    raise ValueError("Collector must return a custom_id starting with the identifier")
                if len(custom_id) > 100:
                    raise ValueError(f"Custom_id is longer than 100, {custom_id=}")
                button.custom_id = custom_id
                return button

            if "on_button_click" not in self.__bot.extra_events:
                self.__bot.extra_events["on_button_click"] = []
            self.__bot.extra_events["on_button_click"].append(check_dyn_button)

            return wrapper

        self._add_button_ident(ident)
        return builder

    def create_modal(
            self,
            ident: str,
            title: str,
            text_inputs: dict[str, DynTextInput],
            collector: Callable[[str, list[str]], str] = base_collector,
            separator: Callable[[str], list[str]] = base_separator
    ) -> Callable[[Callable[Concatenate[ModalInteraction, P], Any]], Callable[P, DynModal]]:
        collision = self._get_modal_ident_collision(ident)
        if collision is not None:
            raise ValueError(f"Ident of modal `{ident}` has collision this `{collision}`")

        if len(text_inputs) > 5:
            raise ValueError(f"Modal has more then 5 text_inputs")

        if len(text_inputs) == 0:
            raise ValueError(f"Modal must have at least 1 text_input")

        def builder(
                func: Callable[Concatenate[ModalInteraction, P], Any]
        ) -> Callable[P, DynModal]:

            _original_sign = inspect.signature(func)

            if len(_original_sign.parameters) < 2:
                raise TypeError(
                    f"Invalid function structure, argument {ModalInteraction} is required in first position, "
                    f"and {dict[str, str]} in second position")

            _first_param, _second_param, *_other_params = _original_sign.parameters.values()
            if _first_param.annotation not in (ModalInteraction, Signature.empty):
                raise TypeError(
                    f"Invalid first argument annotation,"
                    f" it should not be there or its type should be {ModalInteraction}")

            if _second_param.annotation not in (dict[str, str], Signature.empty):
                raise TypeError(
                    f"Invalid first argument annotation,"
                    f" it should not be there or its type should be {dict[str, str]}")

            sign = _original_sign.replace(parameters=_other_params)

            async def check_dyn_modal(inter: ModalInteraction):
                custom_id: str = inter.custom_id  # type: ignore
                if not custom_id.startswith(ident):
                    return
                custom_id_data = separator(custom_id)
                casted_kwargs = self._convert_kwargs_from_strings(sign, custom_id_data)
                await func(inter, inter.text_values, **casted_kwargs)  # type: ignore

            def wrapper(*args: P.args, **kwargs: P.kwargs) -> DynModal:
                # args to kwargs
                casted_kwargs = dict(zip(sign.parameters.keys(), args))
                casted_kwargs.update(kwargs)
                self._args_type_checker(sign, casted_kwargs)

                modal = DynModal(title=title)

                for name, text_input in text_inputs.items():
                    text_input.custom_id = name
                    modal.append_component(text_input)

                custom_id_data = self._convert_kwargs_to_strings_and_sort(sign, casted_kwargs)
                custom_id = collector(ident, custom_id_data)
                if not custom_id.startswith(ident):
                    raise ValueError("Collector must return a custom_id starting with the identifier")
                if len(custom_id) > 100:
                    raise ValueError(f"Custom_id is longer than 100, {custom_id=}")
                modal.custom_id = custom_id
                return modal

            if "on_modal_submit" not in self.__bot.extra_events:
                self.__bot.extra_events["on_modal_submit"] = []
            self.__bot.extra_events["on_modal_submit"].append(check_dyn_modal)

            return wrapper

        self._add_modal_ident(ident)
        return builder

    def create_select_menu(
            self,
            ident: str,
            menu: _DynMenu,
            collector: Callable[[str, list[str]], str] = base_collector,
            separator: Callable[[str], list[str]] = base_separator
    ) -> Callable[[Callable[Concatenate[MessageInteraction, P], Any]], Callable[P, BaseSelect]]:
        collision = self._get_select_menu_ident_collision(ident)
        if collision is not None:
            raise ValueError(f"Ident of modal `{ident}` has collision this `{collision}`")

        def builder(
                func: Callable[Concatenate[MessageInteraction, P], Any]
        ) -> Callable[P, BaseSelect]:

            _original_sign = inspect.signature(func)

            if len(_original_sign.parameters) < 2:
                raise TypeError(
                    f"Invalid function structure, argument {MessageInteraction} is required in first position, "
                    f"and {list} in second position")

            _first_param, _second_param, *_other_params = _original_sign.parameters.values()
            if _first_param.annotation not in (MessageInteraction, Signature.empty):
                raise TypeError(
                    f"Invalid first argument annotation,"
                    f" it should not be there or its type should be {MessageInteraction}")

            if _second_param.annotation not in (list, Signature.empty):
                raise TypeError(
                    f"Invalid first argument annotation,"
                    f" it should not be there or its type should be {list}")

            sign = _original_sign.replace(parameters=_other_params)

            async def check_dyn_select_menu(inter: MessageInteraction):
                custom_id: str = inter.data.custom_id  # type: ignore
                if not custom_id.startswith(ident):
                    return
                custom_id_data = separator(custom_id)
                casted_kwargs = self._convert_kwargs_from_strings(sign, custom_id_data)
                await func(inter, inter.resolved_values, **casted_kwargs)  # type: ignore

            def wrapper(*args: P.args, **kwargs: P.kwargs) -> BaseSelect:
                # args to kwargs
                casted_kwargs = dict(zip(sign.parameters.keys(), args))
                casted_kwargs.update(kwargs)
                self._args_type_checker(sign, casted_kwargs)

                match menu.menu_type:
                    case disnake.ComponentType.string_select:
                        select_menu = StringSelect(
                            placeholder=menu.placeholder,
                            min_values=menu.min_values,
                            max_values=menu.max_values,
                            options=menu.options,
                            disabled=menu.disabled
                        )
                    case disnake.ComponentType.user_select:
                        select_menu = UserSelect(
                            default_values=menu.default_values,
                            placeholder=menu.placeholder,
                            min_values=menu.min_values,
                            max_values=menu.max_values,
                            disabled=menu.disabled
                        )
                    case disnake.ComponentType.role_select:
                        select_menu = RoleSelect(
                            default_values=menu.default_values,
                            placeholder=menu.placeholder,
                            min_values=menu.min_values,
                            max_values=menu.max_values,
                            disabled=menu.disabled
                        )
                    case disnake.ComponentType.mentionable_select:
                        select_menu = MentionableSelect(
                            default_values=menu.default_values,
                            placeholder=menu.placeholder,
                            min_values=menu.min_values,
                            max_values=menu.max_values,
                            disabled=menu.disabled
                        )
                    case disnake.ComponentType.channel_select:
                        select_menu = ChannelSelect(
                            channel_types=menu.channel_types,
                            default_values=menu.default_values,
                            placeholder=menu.placeholder,
                            min_values=menu.min_values,
                            max_values=menu.max_values,
                            disabled=menu.disabled
                        )
                    case _:
                        raise ValueError("User DynModal class for create menu prototype")

                custom_id_data = self._convert_kwargs_to_strings_and_sort(sign, casted_kwargs)
                custom_id = collector(ident, custom_id_data)
                if not custom_id.startswith(ident):
                    raise ValueError("Collector must return a custom_id starting with the identifier")
                if len(custom_id) > 100:
                    raise ValueError(f"Custom_id is longer than 100, {custom_id=}")
                select_menu.custom_id = custom_id
                return select_menu

            if "on_dropdown" not in self.__bot.extra_events:
                self.__bot.extra_events["on_dropdown"] = []
            self.__bot.extra_events["on_dropdown"].append(check_dyn_select_menu)

            return wrapper

        self._add_modal_ident(ident)
        return builder
