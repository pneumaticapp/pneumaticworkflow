import random
import string
from typing import Optional, Tuple

_LETTERS_TYPE = {
    'lower': string.ascii_lowercase,
    'upper': string.ascii_uppercase,
    'digits': string.digits,
}

_DEFAULT_LETTERS = string.ascii_letters + string.digits


class ExcludeLetterError(Exception):
    pass


def get_salt(
    length: int,
    exclude: Optional[Tuple[str]] = None,
):
    letters = _DEFAULT_LETTERS
    if exclude:
        exclude = set(exclude)
        letters = ''.join(
            _LETTERS_TYPE[item] for item in _LETTERS_TYPE
            if item not in exclude
        )
    if not letters:
        raise ExcludeLetterError(
            'Salt should consist at least one type of letters'
        )
    return ''.join(random.choice(letters) for _ in range(0, length))
