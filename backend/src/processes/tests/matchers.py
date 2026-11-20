from typing import List, Tuple


class UnorderedRecipients:
    """Compare exact notification recipients without database row ordering."""

    __hash__ = None

    def __init__(self, *, recipients: List[Tuple[int, str, bool]]):
        self.recipients = sorted(recipients)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, list) and sorted(other) == self.recipients

    def __repr__(self) -> str:
        return f'UnorderedRecipients(recipients={self.recipients!r})'
