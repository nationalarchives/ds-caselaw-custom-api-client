from typing import ClassVar


class Metric:
    """An optional, integer reporting value."""

    key: ClassVar[str]
    title: ClassVar[str]
    description: ClassVar[str]

    def __init__(self, value: int | None = None) -> None:
        self.value = value

    @property
    def value(self) -> int | None:
        return self._value

    @value.setter
    def value(self, value: int | None) -> None:
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError(f"{self.key} must be a non-negative integer or None")
        self._value = value
