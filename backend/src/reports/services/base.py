from abc import ABC, abstractmethod

from django.contrib.auth import get_user_model

UserModel = get_user_model()


class SendDigest(ABC):

    def __init__(self, user_id=None, force=False):
        self._user_id = user_id
        self._force = force
        self._sent_digests_count = 0

    @abstractmethod
    def _fetch_data(self):
        pass

    @abstractmethod
    def _process_data(self, data):
        pass

    def send_digest(self):
        data = self._fetch_data()
        self._process_data(data)
        return self._sent_digests_count
