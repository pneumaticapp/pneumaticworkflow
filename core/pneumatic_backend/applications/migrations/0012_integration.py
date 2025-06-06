# Generated by Django 2.2.16 on 2020-11-24 09:23

from django.db import migrations, models
from pneumatic_backend.generics.mixins.models import SoftDeleteMixin


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('applications', '0011_delete_genericworkflow'),
    ]

    operations = [
        migrations.CreateModel(
            name='Integration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=128)),
                ('logo', models.URLField()),
                ('short_description', models.CharField(max_length=300)),
                ('long_description', models.TextField()),
                ('button_text', models.CharField(max_length=32)),
                ('url', models.URLField()),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['-order'],
            },
            bases=(SoftDeleteMixin, models.Model),
        ),
    ]
