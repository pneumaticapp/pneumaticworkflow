from typing import Optional, Dict
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import (
    ObjectDoesNotExist
)
from django.conf import settings
from django.db import models
from pneumatic_backend.accounts.models import (
    AccountBaseMixin,
)
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.processes.models.mixins import (
    WorkflowMixin,
)
from pneumatic_backend.processes.querysets import (
    TemplateQuerySet,
    FieldTemplateQuerySet,
    TemplateDraftQuerySet,
)
from pneumatic_backend.processes.consts import TEMPLATE_NAME_LENGTH
from pneumatic_backend.processes.enums import (
    PerformerType,
    TemplateType,
)
from pneumatic_backend.authentication.tokens import (
    PublicToken,
    EmbedToken
)
from pneumatic_backend.processes.services.exceptions import (
    EmbedIdCreateMaxDeepException,
    PublicIdCreateMaxDeepException,
)


UserModel = get_user_model()


def get_new_public_id(deep: int = 1):
    if deep > 3:
        raise PublicIdCreateMaxDeepException()
    public_id = str(PublicToken())
    if Template.objects.filter(public_id=public_id).exists():
        public_id = get_new_public_id(deep=deep + 1)
    return public_id


def get_new_embed_id(deep: int = 1):
    if deep > 3:
        raise EmbedIdCreateMaxDeepException()
    embed_id = str(EmbedToken())
    if Template.objects.filter(embed_id=embed_id).exists():
        embed_id = get_new_embed_id(deep=deep + 1)
    return embed_id


class Template(
    SoftDeleteModel,
    WorkflowMixin,
    AccountBaseMixin
):
    name = models.CharField(max_length=TEMPLATE_NAME_LENGTH, default=None)
    generic_name = models.CharField(
        max_length=TEMPLATE_NAME_LENGTH,
        null=True,
        blank=True,
        help_text=(
            'Used in system templates. Possible dynamic values: '
            'account_name, user_first_name, user_last_name, user_email'
        )
    )
    wf_name_template = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    is_embedded = models.BooleanField(default=False)
    public_id = models.CharField(
        max_length=32,
        default=get_new_public_id
    )
    embed_id = models.CharField(
        max_length=32,
        default=get_new_embed_id
    )
    public_success_url = models.TextField(blank=True, null=True)
    template_owners = models.ManyToManyField(
        UserModel,
        related_name='template_owners',
        verbose_name='template owners'
    )
    performers = models.ManyToManyField(
        UserModel,
        related_name='performers',
        verbose_name='All performers for all tasks in the template',
    )
    performers_count = models.IntegerField(default=0)
    tasks_count = models.IntegerField(default=0)
    type = models.CharField(
        choices=TemplateType.CHOICES,
        default=TemplateType.CUSTOM,
        max_length=48
    )
    system_template_id = models.IntegerField(null=True)
    objects = BaseSoftDeleteManager.from_queryset(TemplateQuerySet)()

    search_content = SearchVectorField(null=True)

    date_updated = models.DateTimeField(auto_now=True, null=True)
    updated_by = models.ForeignKey(
        UserModel,
        related_name='workflow_updated_by',
        verbose_name='Updated by',
        on_delete=models.SET_NULL,
        null=True,
    )

    def __str__(self):
        return self.name

    @property
    def public_url(self) -> Optional[str]:
        return f'{settings.PUBLIC_FORMS_ORIGIN}/{self.public_id}'

    @property
    def embed_url(self) -> Optional[str]:
        return f'{settings.PUBLIC_FORMS_ORIGIN}/embed/{self.embed_id}'

    @property
    def kickoff_instance(self):
        return self.kickoff.first()

    def get_draft(self):
        try:
            return self.draft.draft
        except ObjectDoesNotExist:
            return None

    def get_kickoff_output_fields(
        self,
        fields_filter_kwargs: Optional[Dict] = None
    ) -> FieldTemplateQuerySet:

        """ Return the output fields from kickoff """

        try:
            result = self.kickoff.get().fields.all()
            if fields_filter_kwargs:
                result = result.filter(**fields_filter_kwargs)

        except ObjectDoesNotExist:
            from pneumatic_backend.processes.models.templates\
                .fields import FieldTemplate
            result = FieldTemplate.objects.none()
        return result

    def get_tasks_output_fields(
        self,
        tasks_filter_kwargs: Optional[Dict] = None,
        fields_filter_kwargs: Optional[Dict] = None
    ) -> FieldTemplateQuerySet:

        """ Return the output fields from tasks """

        if tasks_filter_kwargs:
            tasks = self.tasks.filter(
                **tasks_filter_kwargs
            )
        else:
            tasks = self.tasks.all()
        tasks_ids = tasks.values_list('id', flat=True)

        if not fields_filter_kwargs:
            fields_filter_kwargs = {}

        from pneumatic_backend.processes.models.templates\
            .fields import FieldTemplate
        return FieldTemplate.objects.filter(
            task_id__in=tasks_ids,
            **fields_filter_kwargs
        )

    def get_tasks(self, performer_id: int):
        from pneumatic_backend.processes.models.templates\
            .task import TaskTemplate

        return TaskTemplate.objects.with_tasks_in_progress(
            template_id=self.id,
            user_id=performer_id,
        )

    @property
    def is_onboarding(self) -> bool:
        return self.type in TemplateType.TYPES_ONBOARDING


class TemplateDraft(SoftDeleteModel):

    draft = JSONField(null=True, blank=True)
    template = models.OneToOneField(
        Template,
        on_delete=models.CASCADE,
        related_name='draft'
    )

    objects = BaseSoftDeleteManager.from_queryset(TemplateDraftQuerySet)()

    @staticmethod
    def _remove_raw_performer_from_list(
        raw_performers: list,
        user_id: int
    ) -> list:
        for num, performer in enumerate(raw_performers):
            if isinstance(performer, dict):
                if performer.get('source_id') == user_id:
                    raw_performers.pop(num)
        return raw_performers

    # pylint: disable=unsubscriptable-object,unsupported-assignment-operation
    def remove_user(self, user_id: int):
        if self.draft is None:
            return

        need_save = False
        template_owners = self.draft.get('template_owners')
        if isinstance(template_owners, list) and user_id in template_owners:
            template_owners.remove(user_id)
            need_save = True

        template_owners = self.draft.get('template_owners')
        if isinstance(template_owners, list) and user_id in template_owners:
            template_owners.remove(user_id)
            need_save = True

        tasks = self.draft.get('tasks')
        if isinstance(tasks, list):
            for task in tasks:
                raw_performers = task.get('raw_performers')
                if isinstance(raw_performers, list):
                    for raw_performer in raw_performers:
                        if (
                            raw_performer['type'] == PerformerType.USER
                            and raw_performer['source_id'] == str(user_id)
                        ):
                            task['raw_performers'].remove(raw_performer)
                            need_save = True

        if need_save:
            self.save(update_fields=('draft',))


class TemplateVersion(SoftDeleteModel):

    version = models.IntegerField(default=0)
    template_id = models.PositiveIntegerField()
    data = JSONField()


class TemplateIntegrations(
    SoftDeleteModel,
    AccountBaseMixin
):

    template = models.OneToOneField(
        Template,
        on_delete=models.CASCADE,
        related_name='integrations'
    )
    shared = models.BooleanField(default=False)
    shared_date = models.DateTimeField(
        null=True,
        verbose_name='Last "shared" activation date'
    )
    api = models.BooleanField(default=False)
    api_date = models.DateTimeField(
        null=True,
        verbose_name='Last "API" activation date'
    )
    zapier = models.BooleanField(default=False)
    zapier_date = models.DateTimeField(
        null=True,
        verbose_name='Last "zapier" activation date'
    )
    webhooks = models.BooleanField(default=False)
    webhooks_date = models.DateTimeField(
        null=True,
        verbose_name='Last "webhooks" activation date'
    )
