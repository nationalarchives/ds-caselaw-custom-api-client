from abc import ABC, abstractmethod
from typing import Any


class IdentifierSchema(ABC):
    """
    A base class which describes what an identifier schema should look like.
    """

    name: str

    def __init_subclass__(cls: type["IdentifierSchema"], **kwargs: Any) -> None:
        for required in (
            "name",
            "namespace",
        ):
            if not getattr(cls, required, False):
                raise NotImplementedError(f"Can't instantiate IdentifierSchema without {required} attribute.")
        super().__init_subclass__(**kwargs)

    def __repr__(self) -> str:
        return self.name

    @classmethod
    @abstractmethod
    def validate_identifier(cls, value: str) -> bool:
        pass


class Identifier(ABC):
    """
    A base class for subclasses representing a concrete identifier.
    """

    schema: type[IdentifierSchema]
    value: str

    def __init_subclass__(cls: type["Identifier"], **kwargs: Any) -> None:
        for required in ("schema",):
            if not getattr(cls, required, False):
                raise NotImplementedError(f"Can't instantiate Identifier without {required} attribute.")
        super().__init_subclass__(**kwargs)

    def __repr__(self) -> str:
        return "self.schema.name: self.value"

    def __init__(self, value: str) -> None:
        self.value = value
