from django.contrib.auth import get_user_model
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models import Q, UniqueConstraint

from src.accounts.models import AccountBaseMixin
from src.ai.enums import (
    AIVendor,
    OpenAiModel,
    OpenAIPromptTarget,
    OpenAIRole,
)
from src.ai.querysets import (
    AIAgentQuerySet,
    AIProviderQuerySet,
    OpenAiPromptMessageQueryset,
    OpenAiPromptQueryset,
)
from src.generics.managers import BaseSoftDeleteManager
from src.generics.mixins.services import EncryptionMixin
from src.generics.models import SoftDeleteModel

UserModel = get_user_model()


class OpenAiPrompt(models.Model):

    class Meta:
        ordering = ('date_created',)

    objects = OpenAiPromptQueryset.as_manager()

    is_active = models.BooleanField(default=True)
    target = models.CharField(
        max_length=200,
        choices=OpenAIPromptTarget.CHOICES,
        default=OpenAIPromptTarget.GET_STEPS,
    )
    model = models.CharField(
        max_length=200,
        choices=OpenAiModel.CHOICES,
        default=OpenAiModel.GPT_35_turbo,
    )
    temperature = models.FloatField(
        default=1,
        validators=(
            MinValueValidator(0),
            MaxValueValidator(2),
        ),
        help_text=(
            'Value between 0 and 2. What sampling temperature to use.'
            'Higher values like 0.8 will make the output more random, '
            'while lower values like 0.2 will make it more focused '
            'and deterministic.'
        ),
    )
    top_p = models.FloatField(
        default=1,
        validators=(
            MinValueValidator(0),
            MaxValueValidator(2),
        ),
        help_text=(
            'Value between 0 and 2. An alternative to sampling with '
            'temperature, called nucleus sampling, where the model considers '
            'the results of the tokens with top_p probability mass. '
            'So 0.1 means only the tokens comprising the top 10% probability '
            'mass are considered. <b>We generally recommend altering this '
            'or temperature but not both.</b>'
        ),
    )
    presence_penalty = models.FloatField(
        default=0,
        validators=(
            MinValueValidator(-2),
            MaxValueValidator(2),
        ),
        help_text=(
            'Value between -2 and 2. APositive values penalize new tokens '
            'based on whether they appear in the text so far, increasing '
            'the model\'s likelihood to talk about new topics. '
            '<a href="https://platform.openai.com/docs/api-reference/'
            'parameter-details">More.</a>'
        ),
    )
    frequency_penalty = models.FloatField(
        default=0,
        validators=(
            MinValueValidator(-2),
            MaxValueValidator(2),
        ),
        help_text=(
            'Value between -2 and 2. Positive values penalize new tokens '
            'based on their existing frequency in the text so far, decreasing '
            'the model\'s likelihood to repeat the same line verbatim. '
            '<a href="https://platform.openai.com/docs/api-reference/'
            'parameter-details">More.</a>'
        ),
    )
    comment = models.TextField(
        blank=True,
        null=True,
        help_text='Optional Notes',
    )
    date_created = models.DateTimeField(auto_now=True)
    date_changed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Prompt №{self.id}'

    def as_dict(self):
        return {
            'target': self.target,
            'model': self.model,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'presence_penalty': self.presence_penalty,
            'frequency_penalty': self.frequency_penalty,
            'messages': [
                {
                    'order': elem.order,
                    'role': elem.role,
                    'content': elem.content,
                }
                for elem in self.messages.active()
            ],
        }


class OpenAiMessage(models.Model):

    class Meta:
        ordering = ('order',)
        verbose_name = 'Prompt message'

    objects = OpenAiPromptMessageQueryset.as_manager()
    is_active = models.BooleanField(
        default=True,
        help_text=(
            'Activation deactivates previous active prompt for the target'
        ),
    )
    order = models.IntegerField(
        validators=(
            MinValueValidator(1),
        ),
    )
    prompt = models.ForeignKey(
        OpenAiPrompt,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    role = models.CharField(
        max_length=100,
        choices=OpenAIRole.CHOICES,
        default=OpenAIRole.USER,
        help_text='The role of the author of this message.',
    )
    content = models.TextField(
        help_text=(
            'The contents of the message. '
            'You should add parameter <b>{{ user_description }}<b> '
            'to the content of one of the messages'
        ),
    )

    def __str__(self):
        return 'Prompt message'


class AIProvider(
    SoftDeleteModel,
    AccountBaseMixin,
    EncryptionMixin,
):

    API_KEY_PREFIX_DISPLAY_LENGTH = 14

    class Meta:
        ordering = ('id',)

    name = models.CharField(
        max_length=255,
        help_text='Display name of the provider',
    )
    base_url = models.URLField(max_length=1024)
    api_key_encrypted = models.TextField()
    vendor = models.CharField(
        max_length=50,
        choices=AIVendor.CHOICES,
        default=AIVendor.OPENAI_COMPATIBLE,
        help_text='Detected vendor of the provider API',
    )
    is_active = models.BooleanField(default=True)

    objects = BaseSoftDeleteManager.from_queryset(AIProviderQuerySet)()

    @property
    def api_key(self) -> str:
        return self.decrypt(self.api_key_encrypted)

    @api_key.setter
    def api_key(self, value: str):
        self.api_key_encrypted = self.encrypt(value)

    @property
    def api_key_prefix(self) -> str:
        return self.api_key[:self.API_KEY_PREFIX_DISPLAY_LENGTH]

    def __str__(self):
        return self.name


class AIAgent(
    SoftDeleteModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ('name',)
        constraints = [
            UniqueConstraint(
                fields=('account', 'name'),
                condition=Q(is_deleted=False),
                name='aiagent_name_account_unique',
            ),
        ]

    name = models.CharField(max_length=255)
    photo = models.URLField(max_length=1024, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    system_prompt = models.TextField(null=False, blank=False)
    provider = models.ForeignKey(
        AIProvider,
        on_delete=models.CASCADE,
        related_name='ai_agents',
        help_text='NULL means the platform default connection',
    )
    model = models.CharField(max_length=200)
    user = models.OneToOneField(
        UserModel,
        on_delete=models.CASCADE,
        related_name='ai_agent',
        help_text='The user the AI agent runs on',
    )

    objects = BaseSoftDeleteManager.from_queryset(AIAgentQuerySet)()

    def __str__(self):
        return self.name
