from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint
from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.processes.models import Template
from src.processes.enums import PresetType
from src.processes.querysets import TemplatePresetQuerySet


UserModel = get_user_model()


class TemplatePreset(SoftDeleteModel, AccountBaseMixin):

    class Meta:
        ordering = ['-date_created']

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='presets',
    )
    author = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='template_presets',
    )
    name = models.CharField(max_length=200)
    is_default = models.BooleanField(default=False)
    type = models.CharField(max_length=20, choices=PresetType.CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)

    objects = BaseSoftDeleteManager.from_queryset(TemplatePresetQuerySet)()


class TemplatePresetField(models.Model):

    class Meta:
        ordering = ['api_name']
        constraints = [
            UniqueConstraint(
                fields=['preset', 'api_name'],
                name='processes_templatepresetfield_preset_api_name_unique',
            )
        ]

    preset = models.ForeignKey(
        TemplatePreset,
        on_delete=models.CASCADE,
        related_name='fields',
    )
    api_name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    width = models.IntegerField(default=100)
