from abc import ABC, abstractmethod
from typing import Any, Dict


class EmailClient(ABC):

    @abstractmethod
    def send_email(
        self,
        to: str,
        template_code: str,
        message_data: Dict[str, Any],
        user_id: int,
    ) -> None:
        pass
