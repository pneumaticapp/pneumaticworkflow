from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0250_add_fieldsets'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldsettemplate',
            name='template',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='fieldsets',
                to='processes.Template',
            ),
        ),
        migrations.AddField(
            model_name='fieldsettemplate',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='fieldsettemplate',
            name='label_position',
            field=models.CharField(
                choices=[('top', 'Top'), ('left', 'Left')],
                default='top',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='fieldsettemplate',
            name='layout',
            field=models.CharField(
                choices=[
                    ('horizontal', 'Horizontal'),
                    ('vertical', 'Vertical'),
                ],
                default='vertical',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='fieldset',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='fieldset',
            name='label_position',
            field=models.CharField(
                choices=[('top', 'Top'), ('left', 'Left')],
                default='top',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='fieldset',
            name='layout',
            field=models.CharField(
                choices=[
                    ('horizontal', 'Horizontal'),
                    ('vertical', 'Vertical'),
                ],
                default='vertical',
                max_length=20,
            ),
        ),
    ]
