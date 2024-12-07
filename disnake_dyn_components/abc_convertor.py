from abc import ABC, abstractmethod
from typing import Any


__all__ = ["Convertor"]


class Convertor(ABC):

    @staticmethod
    @abstractmethod
    def to_string(value: Any) -> str:
        ...

    @staticmethod
    @abstractmethod
    def from_string(string: str) -> Any:
        ...
