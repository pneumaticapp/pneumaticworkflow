from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0004_add_ai_agent'),
    ]

    operations = [
        migrations.RenameField(
            model_name='aiprovider',
            old_name='vendor',
            new_name='type',
        ),
        migrations.AlterField(
            model_name='aiprovider',
            name='type',
            field=models.CharField(
                choices=[
                    ('openai', 'OpenAI'),
                    ('openrouter', 'OpenRouter'),
                    ('anthropic', 'Anthropic'),
                    ('gemini', 'Gemini'),
                    ('groq', 'Groq'),
                    ('xai', 'xAI'),
                    ('together', 'Together'),
                    ('fireworks', 'Fireworks'),
                    ('deepseek', 'DeepSeek'),
                    ('mistral', 'Mistral'),
                    ('cerebras', 'Cerebras'),
                    ('perplexity', 'Perplexity'),
                    ('huggingface', 'Hugging Face'),
                    ('sambanova', 'SambaNova'),
                    ('nvidia_nim', 'NVIDIA NIM'),
                    ('cursor', 'Cursor'),
                ],
                default='openai',
                help_text='Detected type of the provider API',
                max_length=50,
            ),
        ),
    ]
