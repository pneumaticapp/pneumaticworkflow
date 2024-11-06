# pylint: disable=not-callable
from typing import Union, Optional
from django.core.cache import caches
from rest_framework.serializers import ModelSerializer
from django.db.models import Model


class BaseClsCache:

    cache = caches['default']
    serializer_cls: Optional[ModelSerializer] = None
    cache_timeout = None

    @classmethod
    def _serialize_value(
        cls,
        value: Union[str, dict]
    ) -> str:

        """ Django cache framework serialize
            any picklable Python object

            Otherwise, override this method """

        return value

    @classmethod
    def _serialize_instance(
        cls,
        instance: Model
    ) -> dict:

        if cls.serializer_cls is None:
            raise Exception('Must define a serializer class before use.')
        return cls.serializer_cls(instance=instance).data

    @classmethod
    def _deserialize_value(
        cls,
        value: Optional[str]
    ) -> Union[str, dict, None]:

        """ Django cache framework deserialize
            any picklable Python object

            Otherwise, override this method """

        return value

    @classmethod
    def _set_cache_value(
        cls,
        value: Union[str, int, dict, list, Model],
        key: str
    ):
        if isinstance(value, Model):
            value = cls._serialize_instance(value)

        cls.cache.set(
            key=key,
            value=cls._serialize_value(value),
            timeout=cls.cache_timeout
        )
        return value

    @classmethod
    def _get_cache_value(
        cls,
        key: str,
        default: Union[str, int, dict, list, None] = None
    ):
        str_value = cls.cache.get(key=key, default=default)
        return cls._deserialize_value(str_value)

    @classmethod
    def _delete_cache_value(
        cls,
        key: str
    ) -> bool:
        return cls.cache.delete(key=key)


class DefaultClsCacheMixin(BaseClsCache):

    """ Use if one cache key is enough """

    default_cache_key: str = None

    @classmethod
    def _set_cache(
        cls,
        value: Union[str, int, dict, list, Model],
    ) -> Union[str, int, dict, list]:

        return cls._set_cache_value(
            key=cls.default_cache_key,
            value=value,
        )

    @classmethod
    def _get_cache(
        cls,
        default: Union[str, int, dict, list, None] = None
    ) -> Union[str, int, dict, list, None]:

        return cls._get_cache_value(
            key=cls.default_cache_key,
            default=default
        )

    @classmethod
    def _delete_cache(cls) -> bool:
        return cls._delete_cache_value(
            key=cls.default_cache_key
        )


class ClsCacheMixin(BaseClsCache):

    """ Use if you need a different cache keys for different instances """

    cache_key_prefix = None

    @classmethod
    def _get_cache_key(
        cls,
        key: Union[str, int]
    ) -> str:
        return f'{cls.cache_key_prefix}:{key}'

    @classmethod
    def _set_cache(
        cls,
        value: Union[str, int, dict, list, Model],
        key: Union[str, int]
    ) -> Union[str, int, dict, list]:

        return cls._set_cache_value(
            key=cls._get_cache_key(key),
            value=value,
        )

    @classmethod
    def _get_cache(
        cls,
        key: Union[str, int],
        default: Union[str, int, dict, list, None] = None
    ) -> Union[str, int, dict, list, None]:

        return cls._get_cache_value(
            key=cls._get_cache_key(key),
            default=default
        )

    @classmethod
    def _delete_cache(
        cls,
        key: Union[str, int]
    ) -> bool:
        return cls._delete_cache_value(
            key=cls._get_cache_key(key),
        )


class CacheMixin(BaseClsCache):

    cache_key_prefix = None
    cache = caches['default']
    serializer_cls: Optional[ModelSerializer] = None
    cache_timeout = None

    def _serialize_value(
        self,
        value: Union[str, dict]
    ) -> str:

        """ Django cache framework serialize
            any picklable Python object

            Otherwise, override this method """

        return value

    def _serialize_instance(
        self,
        instance: Model
    ) -> dict:

        if self.serializer_cls is None:
            raise Exception('Must define a serializer class before use.')
        return self.serializer_cls(instance=instance).data

    def _deserialize_value(
        self,
        value: Optional[str]
    ) -> Union[str, dict, None]:

        """ Django cache framework deserialize
            any picklable Python object

            Otherwise, override this method """

        return value

    def _set_cache_value(
        self,
        value: Union[str, int, dict, list, Model],
        key: str
    ):
        if isinstance(value, Model):
            value = self._serialize_instance(value)

        self.cache.set(
            key=key,
            value=self._serialize_value(value),
            timeout=self.cache_timeout
        )
        return value

    def _get_cache_value(
        self,
        key: str,
        default: Union[str, int, dict, list, None] = None
    ):
        str_value = self.cache.get(key=key, default=default)
        return self._deserialize_value(str_value)

    def _delete_cache_value(
        self,
        key: str
    ) -> bool:
        return self.cache.delete(key=key)

    def _get_cache_key(
        self,
        key: Union[str, int]
    ) -> str:
        return f'{self.cache_key_prefix}:{key}'

    def _set_cache(
        self,
        value: Union[str, int, dict, list, Model],
        key: Union[str, int]
    ) -> Union[str, int, dict, list]:

        return self._set_cache_value(
            key=self._get_cache_key(key),
            value=value,
        )

    def _get_cache(
        self,
        key: Union[str, int],
        default: Union[str, int, dict, list, None] = None
    ) -> Union[str, int, dict, list, None]:

        return self._get_cache_value(
            key=self._get_cache_key(key),
            default=default
        )

    def _delete_cache(
        self,
        key: Union[str, int]
    ) -> bool:
        return self._delete_cache_value(
            key=self._get_cache_key(key),
        )
