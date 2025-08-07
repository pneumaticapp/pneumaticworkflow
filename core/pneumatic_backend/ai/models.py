from django.db import models
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator
)
from pneumatic_backend.ai.enums import (
    OpenAiModel,
    OpenAIRole,
    OpenAIPromptTarget,
)
from pneumatic_backend.ai.querysets import (
    OpenAiPromptQueryset,
    OpenAiPromptMessageQueryset
)


class OpenAiPrompt(models.Model):

    class Meta:
        ordering = ('date_created',)

    objects = OpenAiPromptQueryset.as_manager()

    is_active = models.BooleanField(default=True)
    target = models.CharField(
        max_length=200,
        choices=OpenAIPromptTarget.CHOICES,
        default=OpenAIPromptTarget.GET_STEPS
    )
    model = models.CharField(
        max_length=200,
        choices=OpenAiModel.CHOICES,
        default=OpenAiModel.GPT_35_turbo
    )
    temperature = models.FloatField(
        default=1,
        validators=(
            MinValueValidator(0),
            MaxValueValidator(2)
        ),
        help_text=(
            'Value between 0 and 2. What sampling temperature to use.'
            'Higher values like 0.8 will make the output more random, '
            'while lower values like 0.2 will make it more focused '
            'and deterministic.'
        )
    )
    top_p = models.FloatField(
        default=1,
        validators=(
            MinValueValidator(0),
            MaxValueValidator(2)
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
            MaxValueValidator(2)
        ),
        help_text=(
            'Value between -2 and 2. APositive values penalize new tokens '
            'based on whether they appear in the text so far, increasing '
            'the model\'s likelihood to talk about new topics. '
            '<a href="https://platform.openai.com/docs/api-reference/'
            'parameter-details">More.</a>'
        )
    )
    frequency_penalty = models.FloatField(
        default=0,
        validators=(
            MinValueValidator(-2),
            MaxValueValidator(2)
        ),
        help_text=(
            'Value between -2 and 2. Positive values penalize new tokens '
            'based on their existing frequency in the text so far, decreasing '
            'the model\'s likelihood to repeat the same line verbatim. '
            '<a href="https://platform.openai.com/docs/api-reference/'
            'parameter-details">More.</a>'
        )
    )
    comment = models.TextField(
        blank=True,
        null=True,
        help_text='Optional Notes'
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
            ]
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
        )
    )
    order = models.IntegerField(
        validators=(
            MinValueValidator(1),
        )
    )
    prompt = models.ForeignKey(
        OpenAiPrompt,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(
        max_length=100,
        choices=OpenAIRole.CHOICES,
        default=OpenAIRole.USER,
        help_text='The role of the author of this message.'
    )
    content = models.TextField(
        help_text=(
            'The contents of the message. '
            'You should add parameter <b>{{ user_description }}<b> '
            'to the content of one of the messages'
        )
    )

    def __str__(self):
        return f'Prompt message'
