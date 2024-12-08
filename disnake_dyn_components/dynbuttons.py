from disnake.ext.commands.common_bot_base import CommonBotBase
from disnake import ButtonStyle, Emoji, PartialEmoji
from disnake.interactions.message import MessageInteraction
from disnake.ui import Button
from typing import Optional, Union, Callable, Concatenate, ParamSpec, Any
import logging
import inspect
from inspect import Signature, Parameter

from .abc_convertor import Convertor


__all__ = ["DynButtons"]


log = logging.getLogger(__name__)


P = ParamSpec("P")


class DynButtons:

    def __init__(self, bot: CommonBotBase):
        self.__bot = bot
        self.__buttons_ident_list: list[str] = []  # ident list for find collisions

    def _add_ident(self, ident: str):
        self.__buttons_ident_list.append(ident)

    def _delete_ident(self, ident: str):
        self.__buttons_ident_list.remove(ident)

    def _get_ident_collision(self, ident: str) -> Optional[str]:
        """
        :return: string identifier with which the collision was found, otherwise None
        """
        for register_ident in self.__buttons_ident_list:
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

        # # args count test
        # sign_len = len(sign.parameters)
        # args_len = len(casted_kwargs)
        # if sign_len != args_len:
        #     raise TypeError(f"Button builder expects {sign_len} arguments but gets {args_len}")

        # kwargs types check
        for param_name, value in casted_kwargs.items():
            param = params.get(param_name)
            if param is None:
                raise TypeError(f"Button builder does not have key word argument `{param_name}`")
            elif param.annotation is Signature.empty:
                log.warning(f"Dynamic button parameter `{param_name}` has not type and will be casting to string")
            elif issubclass(param.annotation, Convertor):
                ...
            elif not isinstance(value, (param.annotation, Convertor)):
                raise TypeError(
                    f"Button builder expects argument `{param_name}`"
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
    ) -> Callable[[Callable[Concatenate[MessageInteraction, P], Any]], Callable[P, Button]]:
        collision = self._get_ident_collision(ident)
        if collision is not None:
            raise ValueError(f"Ident of button `{ident}` has collision this `{collision}`")

        if style is ButtonStyle.url or style is ButtonStyle.link:
            raise ValueError("Dyn buttons do not support url or link style")

        def builder(
                func: Callable[Concatenate[MessageInteraction, P], Any]
        ) -> Callable[P, Button]:

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

            async def check_dyn_buttons(inter: MessageInteraction):
                custom_id: str = inter.component.custom_id  # type: ignore
                if not custom_id.startswith(ident):
                    return
                custom_id_data = separator(custom_id)
                casted_kwargs = self._convert_kwargs_from_strings(sign, custom_id_data)
                await func(inter, **casted_kwargs)  # type: ignore

            self.__bot.add_listener(check_dyn_buttons, "on_button_click")

            def wrapper(*args: P.args, **kwargs: P.kwargs) -> Button:
                # args to kwargs
                casted_kwargs = dict(zip(sign.parameters.keys(), args))
                casted_kwargs.update(kwargs)
                self._args_type_checker(sign, casted_kwargs)

                button = Button(style=style, label=label, disabled=disabled, emoji=emoji, row=row)
                custom_id_data = self._convert_kwargs_to_strings_and_sort(sign, casted_kwargs)
                custom_id = collector(ident, custom_id_data)
                if not custom_id.startswith(ident):
                    raise ValueError("Collector must return a custom_id starting with the identifier")
                if len(custom_id) > 100:
                    raise ValueError(f"Custom_id is longer than 100, {custom_id=}")
                button.custom_id = custom_id
                return button

            return wrapper

        self._add_ident(ident)
        return builder
