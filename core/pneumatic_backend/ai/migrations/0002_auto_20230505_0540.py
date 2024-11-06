# Generated by Django 2.2 on 2023-05-05 05:40

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openaimessage',
            name='content',
            field=models.TextField(help_text='The contents of the message. You should add parameter <b>{{ user_description }}<b> to the content of one of the messages'),
        ),
        migrations.AlterField(
            model_name='openaimessage',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Activation deactivates previous active prompt for the target'),
        ),
        migrations.AlterField(
            model_name='openaimessage',
            name='prompt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='ai.OpenAiPrompt'),
        ),
        migrations.AlterField(
            model_name='openaiprompt',
            name='frequency_penalty',
            field=models.FloatField(default=0, help_text='Value between -2 and 2. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model\'s likelihood to repeat the same line verbatim. <a href="https://platform.openai.com/docs/api-reference/parameter-details">More.</a>', validators=[django.core.validators.MinValueValidator(-2), django.core.validators.MaxValueValidator(2)]),
        ),
        migrations.AlterField(
            model_name='openaiprompt',
            name='presence_penalty',
            field=models.FloatField(default=0, help_text='Value between -2 and 2. APositive values penalize new tokens based on whether they appear in the text so far, increasing the model\'s likelihood to talk about new topics. <a href="https://platform.openai.com/docs/api-reference/parameter-details">More.</a>', validators=[django.core.validators.MinValueValidator(-2), django.core.validators.MaxValueValidator(2)]),
        ),
        migrations.AlterField(
            model_name='openaiprompt',
            name='temperature',
            field=models.FloatField(default=1, help_text='Value between 0 and 2. What sampling temperature to use.Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)]),
        ),
        migrations.AlterField(
            model_name='openaiprompt',
            name='top_p',
            field=models.FloatField(default=1, help_text='Value between 0 and 2. An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered. <b>We generally recommend altering this or temperature but not both.</b>', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)]),
        ),
    ]