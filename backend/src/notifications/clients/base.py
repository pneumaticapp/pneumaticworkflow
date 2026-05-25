from abc import ABC, abstractmethod
from typing import Any, Dict


class EmailClient(ABC):

    def __init__(self, account_id: int):
        self.account_id = account_id

    @abstractmethod
    def send_email(
        self,
        to: str,
        template_code: str,
        message_data: Dict[str, Any],
        user_id: int,
    ) -> None:
        pass
