from typing import List, Optional, Union


class Comparator:
    @classmethod
    def equals(cls, a, b):
        return a == b

    @classmethod
    def not_equals(cls, a, b):
        return not cls.equals(a, b)

    @classmethod
    def contains(
        cls,
        container: Optional[List[Union[int, str]]],
        item: Optional[Union[int, str]],
    ):
        if item is None or container is None:
            return False
        return item in container

    @classmethod
    def not_contains(
        cls,
        container: Optional[List[Union[int, str]]],
        item: Optional[Union[int, str]],
    ):
        if item is None or container is None:
            return False
        return not cls.contains(container, item)

    @classmethod
    def exists(cls, a):
        if a is None:
            return False
        if a == 0:
            return True
        return bool(a)

    @classmethod
    def not_exists(cls, a):
        return not cls.exists(a)

    @classmethod
    def more_than(cls, a, b):
        if a is None or b is None:
            return False
        return a > b

    @classmethod
    def less_than(cls, a, b):
        if a is None or b is None:
            return False
        return a < b

    @classmethod
    def completed(cls, a: bool):
        return a
