import re
import json
from django.http import QueryDict
from django.core.files import File
from django.utils.datastructures import MultiValueDict
from django.conf import settings
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ParseError


class CamelCaseJSONParser(JSONParser):

    """
        Convert camelCase to snake_case
        Source https://github.com/vbabiy/djangorestframework-camel-case

        Config:
        no_underscore_before_number: bool - convention of snake case:
            value=False: v2Counter -> v_2_counter
            value=True: v2Counter -> v2_counter
        ignore_fields: tuple - fields which should not have their data changed.
            init data = {"myKey": {"doNotChange": 1}}
            value=None: {"my_key": {"do_not_change": 1}}
            value=("myKey",): {"my_key": {"doNotChange": 1}}
        ignore_keys: tuple - specify keys which should not be renamed.

    """

    JSON_UNDERSCOREIZE = {
        "no_underscore_before_number": False,
        "ignore_fields": None,
        "ignore_keys": None,
    }

    def get_underscoreize_re(self):
        if self.JSON_UNDERSCOREIZE["no_underscore_before_number"]:
            pattern = r"([a-z0-9]|[A-Z]?(?=[A-Z](?=[a-z])))([A-Z])"
        else:
            pattern = (
                r"([a-z0-9]|[A-Z]?(?=[A-Z0-9](?=[a-z0-9]|(?<![A-Z])$)))([A-Z]"
                r"|(?<=[a-z])[0-9](?=[0-9A-Z]|$)|(?<=[A-Z])[0-9](?=[0-9]|$))"
            )
        return re.compile(pattern)

    def camel_to_underscore(self, name):
        underscoreize_re = self.get_underscoreize_re()
        return underscoreize_re.sub(r"\1_\2", name).lower()

    def _get_iterable(self, data):
        if isinstance(data, QueryDict):
            return data.lists()
        else:
            return data.items()

    def is_iterable(self, obj):
        try:
            iter(obj)
        except TypeError:
            return False
        else:
            return True

    def underscoreize(self, data):
        ignore_fields = self.JSON_UNDERSCOREIZE.get("ignore_fields") or ()
        ignore_keys = self.JSON_UNDERSCOREIZE.get("ignore_keys") or ()
        if isinstance(data, dict):
            new_dict = {}
            if type(data) == MultiValueDict:
                new_data = MultiValueDict()
                for key, value in data.items():
                    new_data.setlist(
                        self.camel_to_underscore(key),
                        data.getlist(key)
                    )
                return new_data
            for key, value in self._get_iterable(data):
                if isinstance(key, str):
                    new_key = self.camel_to_underscore(key)
                else:
                    new_key = key

                if key not in ignore_fields and new_key not in ignore_fields:
                    result = self.underscoreize(value)
                else:
                    result = value
                if key in ignore_keys or new_key in ignore_keys:
                    new_dict[key] = result
                else:
                    new_dict[new_key] = result

            if isinstance(data, QueryDict):
                new_query = QueryDict(mutable=True)
                for key, value in new_dict.items():
                    new_query.setlist(key, value)
                return new_query
            return new_dict
        if self.is_iterable(data) and not isinstance(data, (str, File)):
            return [self.underscoreize(item) for item in data]

        return data

    def parse(self, stream, media_type=None, parser_context=None):
        parser_context = parser_context or {}
        encoding = parser_context.get("encoding", settings.DEFAULT_CHARSET)

        try:
            data = stream.read().decode(encoding)
            return self.underscoreize(json.loads(data))
        except ValueError as exc:
            raise ParseError("JSON parse error - %s" % str(exc))
