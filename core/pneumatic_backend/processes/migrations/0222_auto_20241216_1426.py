# Generated by Django 2.2 on 2024-12-16 09:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import pneumatic_backend.generics.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0130_add_user_groups'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('processes', '0221_auto_20250206_1222'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemplateOwner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('api_name', models.CharField(max_length=200)),
                ('type', models.CharField(choices=[('user', 'user'), ('group', 'group')], max_length=100)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
                ('group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.UserGroup')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owners', to='processes.Template')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['type'],
            },
            bases=(pneumatic_backend.generics.mixins.models.SoftDeleteMixin, models.Model),
        ),
        migrations.AddConstraint(
            model_name='templateowner',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_deleted=False),
                fields=('template', 'api_name'),
                name='processes_template_owner_template_api_name_unique'
            ),
        ),
        migrations.AddField(
            model_name='workflow',
            name='owners',
            field=models.ManyToManyField(related_name='owners', to=settings.AUTH_USER_MODEL, verbose_name='owners'),
        ),
    ]
