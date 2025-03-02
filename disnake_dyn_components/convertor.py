from typing import Any, Protocol, runtime_checkable


__all__ = ["Convertor"]


@runtime_checkable
class Convertor(Protocol):

    @staticmethod
    def to_string(value: Any) -> str:
        ...

    @staticmethod
    def from_string(string: str) -> Any:
        ...
