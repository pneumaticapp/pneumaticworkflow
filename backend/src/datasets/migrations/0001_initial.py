# Generated migration for src.datasets app

from django.db import migrations, models
import django.db.models.deletion
import src.generics.mixins.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0141_notification_text_default'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, default='')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
            ],
            options={
                'ordering': ['-id'],
            },
            bases=(src.generics.mixins.models.SoftDeleteMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DatasetItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('value', models.CharField(max_length=200)),
                ('order', models.IntegerField(default=0)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='datasets.Dataset')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
            ],
            options={
                'ordering': ['order', 'id'],
            },
            bases=(src.generics.mixins.models.SoftDeleteMixin, models.Model),
        ),
        migrations.AddConstraint(
            model_name='dataset',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_deleted=False),
                fields=['account', 'name'],
                name='dataset_account_name_unique',
            ),
        ),
        migrations.AddConstraint(
            model_name='datasetitem',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_deleted=False),
                fields=['dataset', 'value'],
                name='datasetitem_dataset_value_unique',
            ),
        ),
    ]
