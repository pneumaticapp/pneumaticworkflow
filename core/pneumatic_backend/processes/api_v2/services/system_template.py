from typing import List, Dict
from django.db import transaction
from django.contrib.auth import get_user_model
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.entities import (
    LibraryTemplateData,
)
from pneumatic_backend.processes.enums import SysTemplateType
from pneumatic_backend.processes.models import (
    SystemTemplate,
    SystemTemplateCategory
)

UserModel = get_user_model()


class SystemTemplateService:

    def __init__(
        self,
        user: UserModel,
        is_superuser: bool = False,
        auth_type: AuthTokenType.LITERALS = AuthTokenType.USER
    ):
        self.user = user
        self.account = user.account
        self.is_superuser = is_superuser
        self.auth_type = auth_type

    def _get_categories_dict(
        self,
        data: List[LibraryTemplateData]
    ) -> Dict[str, int]:

        """ Create not existent categories and return dict with {name: id} """

        names = {elem['category'].strip() for elem in data}
        category_by_name = {
            elem.name: elem.id
            for elem in SystemTemplateCategory.objects.filter(
                name__in=names
            ).only('id', 'name')
        }
        if len(names) != len(category_by_name.keys()):
            names -= set(category_by_name.keys())
            order = SystemTemplateCategory.objects.max_order() + 1
            for name in names:
                category = SystemTemplateCategory.objects.create(
                    name=name,
                    is_active=False,
                    order=order
                )
                category_by_name[name] = category.id
                order += 1
        return category_by_name

    def import_library_templates(
        self,
        data: List[LibraryTemplateData]
    ):

        """ Create or update library templates by name """

        category_by_name = self._get_categories_dict(data)
        data_by_name = {elem['name'].strip(): elem for elem in data}

        with transaction.atomic():
            # update existent sys templates
            for sys_template in SystemTemplate.objects.filter(
                name__in=data_by_name.keys(),
                type=SysTemplateType.LIBRARY
            ):
                data = data_by_name[sys_template.name]
                sys_template.name = data['name']
                sys_template.description = data['description']
                sys_template.category_id = category_by_name[data['category']]
                sys_template.template = {
                    'name': data['name'],
                    'description': data['description'],
                    'kickoff': data['kickoff'],
                    'tasks': data['tasks'],
                }
                sys_template.save()
                del data_by_name[sys_template.name]

            # create new sys templates
            sys_templates = []
            for name, data in data_by_name.items():
                sys_templates.append(
                    SystemTemplate(
                        is_active=True,
                        name=name,
                        type=SysTemplateType.LIBRARY,
                        description=data['description'],
                        category_id=category_by_name[data['category']],
                        template={
                            'name': name,
                            'description': data['description'],
                            'kickoff': data['kickoff'],
                            'tasks': data['tasks'],
                        }
                    )
                )
            SystemTemplate.objects.bulk_create(sys_templates, batch_size=1000)
