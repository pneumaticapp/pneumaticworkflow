from django.db import models

from pneumatic_backend.applications.querysets import IntegrationsQuerySet
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.generics.managers import BaseSoftDeleteManager


class Integration(SoftDeleteModel):
    name = models.CharField(
        max_length=128,
        help_text='Name of service'
    )
    logo = models.URLField()
    short_description = models.CharField(
        max_length=300,
        help_text='Short description of service we integrated with.'
    )
    long_description = models.TextField(
        help_text='Long description on page of the integration. '
                  'You can use HTML markup here.'
    )
    button_text = models.CharField(
        max_length=32,
        help_text='Text that will be shown on the button, '
                  'that redirect user to the service page.'
    )
    url = models.URLField(
        help_text='URL to the service'
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text='Integration order. The higher the number here '
                  'the higher integration in integrations list.'
    )
    is_active = models.BooleanField(
        default=False,
        help_text='Make it active if you are sure, '
                  'that the integration is ready.'
    )

    objects = BaseSoftDeleteManager.from_queryset(IntegrationsQuerySet)()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-order']
