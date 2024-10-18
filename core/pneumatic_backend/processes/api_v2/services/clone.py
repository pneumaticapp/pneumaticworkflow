from typing import Dict, Any, List
from pneumatic_backend.processes.consts import TEMPLATE_NAME_LENGTH
from pneumatic_backend.processes.utils.common import (
    string_abbreviation,
)


class CloneService:

    @classmethod
    def _get_dict_clone(cls, data: Dict[str, Any]) -> Dict[str, Any]:

        data.pop('id', None)

        for key, value in data.items():
            if isinstance(value, list):
                data[key] = cls._get_list_clone(value)
            elif isinstance(value, dict):
                data[key] = cls._get_dict_clone(value)
        return data

    @classmethod
    def _get_list_clone(cls, data: List[Any]) -> List[Any]:

        for num, elem in enumerate(data):
            if isinstance(elem, dict):
                data[num] = cls._get_dict_clone(elem)
            elif isinstance(elem, list):
                data[num] = cls._get_list_clone(elem)
        return data

    @classmethod
    def get_template_draft_clone(
        cls,
        draft: Dict[str, Any]
    ) -> Dict[str, Any]:

        """ Return clone of all template data.
            For "clone" clears identifiers,
            and changes API names to new ones """

        clone = cls._get_dict_clone(draft)
        clone['name'] = string_abbreviation(
            name=clone.get('name', ''),
            length=TEMPLATE_NAME_LENGTH,
            postfix=' - clone',
        )
        clone['is_active'] = False
        return clone
