# Generated by Django 2.2.17 on 2021-04-19 07:47

from django.db import migrations, models
import django.db.models.deletion
import pneumatic_backend.accounts.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0069_auto_20210217_1417'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountSignupData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('utm_source', pneumatic_backend.accounts.fields.TruncatingCharField(blank=True, max_length=32, null=True)),
                ('utm_medium', pneumatic_backend.accounts.fields.TruncatingCharField(blank=True, max_length=32, null=True)),
                ('utm_campaign', pneumatic_backend.accounts.fields.TruncatingCharField(blank=True, max_length=64, null=True)),
                ('utm_term', pneumatic_backend.accounts.fields.TruncatingCharField(blank=True, max_length=128, null=True)),
                ('utm_content', pneumatic_backend.accounts.fields.TruncatingCharField(blank=True, max_length=256, null=True)),
                ('gclid', models.CharField(blank=True, max_length=100, null=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
            ],
        ),
    ]