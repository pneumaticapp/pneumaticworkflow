from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0251_add_skip_for_starter'),
    ]

    operations = [
        migrations.AddField(
            model_name='rawperformertemplate',
            name='source_task_api_name',
            field=models.CharField(
                blank=True,
                max_length=200,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='rawperformer',
            name='source_task_api_name',
            field=models.CharField(
                blank=True,
                max_length=200,
                null=True,
            ),
        ),
    ]
