# Generated by Django 2.2.5 on 2019-10-03 04:14

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20191002_1210'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(max_length=32, unique=True, validators=[django.core.validators.RegexValidator(message='Phone number must be entered in the format: "+99999999999". Up to 15 digits allowed.', regex='^\\+?1?\\d{9,15}$')]),
        ),
        migrations.CreateModel(
            name='GoogleAuth',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=128, null=True)),
                ('last_name', models.CharField(blank=True, max_length=128, null=True)),
                ('phone', models.CharField(blank=True, max_length=32, null=True)),
                ('company', models.CharField(blank=True, max_length=128, null=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
