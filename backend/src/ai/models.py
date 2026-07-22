from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models

from src.ai.enums import (
    AITaskRunStatus,
    OpenAiModel,
    OpenAIPromptTarget,
    OpenAIRole,
)
from src.ai.querysets import (
    AIAgentQuerySet,
    AIProviderConnectionQuerySet,
    OpenAiPromptMessageQueryset,
    OpenAiPromptQueryset,
)
from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel


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


class AIProviderConnection(SoftDeleteModel):

    """ Account-scoped credentials for an OpenAI-compatible endpoint.

        Phase 1 ships the table only: every agent uses the implicit
        platform connection whose key comes from settings. Customer
        (BYO) rows arrive in Phase 2 together with key encryption. """

    class Meta:
        ordering = ('id',)

    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='ai_provider_connections',
    )
    name = models.CharField(max_length=255)
    base_url = models.URLField(
        max_length=1024,
        default='https://openrouter.ai/api/v1',
    )
    api_key = models.CharField(max_length=1024)
    is_active = models.BooleanField(default=True)

    objects = BaseSoftDeleteManager.from_queryset(
        AIProviderConnectionQuerySet,
    )()

    def __str__(self):
        return self.name


class AIAgent(SoftDeleteModel):

    """ A named, reusable AI performer: which model it talks to and
        the role it plays. Holds no credentials — connections are
        account-scoped. """

    class Meta:
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('account', 'name'),
                condition=models.Q(is_deleted=False),
                name='aiagent_name_account_unique',
            ),
        ]

    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='ai_agents',
    )
    name = models.CharField(max_length=255)
    model_slug = models.CharField(
        max_length=200,
        help_text='OpenRouter-style model slug, e.g. anthropic/claude-3',
    )
    system_prompt = models.TextField(blank=True, default='')
    temperature = models.FloatField(
        null=True,
        blank=True,
        validators=(
            MinValueValidator(0),
            MaxValueValidator(2),
        ),
        help_text='NULL means the provider default',
    )
    max_tokens = models.IntegerField(
        null=True,
        blank=True,
        validators=(
            MinValueValidator(1),
        ),
        help_text='NULL means the provider default',
    )
    connection = models.ForeignKey(
        AIProviderConnection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_agents',
        help_text='NULL means the platform default connection',
    )
    photo = models.URLField(max_length=1024, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = BaseSoftDeleteManager.from_queryset(AIAgentQuerySet)()

    def __str__(self):
        return self.name


class AITaskRun(models.Model):

    """ One row per (task, agent) execution attempt-set: the
        idempotency claim (get_or_create), audit record and metering
        source. A task return resets the row so the agent re-runs on
        reactivation. """

    class Meta:
        ordering = ('-date_created',)
        unique_together = ('task', 'agent')

    task = models.ForeignKey(
        'processes.Task',
        on_delete=models.CASCADE,
        related_name='ai_task_runs',
    )
    agent = models.ForeignKey(
        AIAgent,
        on_delete=models.CASCADE,
        related_name='task_runs',
    )
    status = models.CharField(
        max_length=32,
        choices=AITaskRunStatus.CHOICES,
        default=AITaskRunStatus.QUEUED,
    )
    reason = models.TextField(
        null=True,
        blank=True,
        help_text='Why the task was left for a human or failed',
    )
    model_used = models.CharField(max_length=200, null=True, blank=True)
    prompt_tokens = models.IntegerField(null=True, blank=True)
    completion_tokens = models.IntegerField(null=True, blank=True)
    attempts = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    date_completed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'AITaskRun {self.id}'
