# Generated manually on 2026-02-27 18:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import src.generics.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0139_remove_account_external_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('processes', '0241_auto_20260226_0122'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemplateStarter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('api_name', models.CharField(max_length=200)),
                ('type', models.CharField(choices=[('user', 'user'), ('group', 'group')], max_length=100)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
                ('group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.UserGroup')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='starters', to='processes.Template')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['type', 'id'],
            },
            bases=(src.generics.mixins.models.SoftDeleteMixin, models.Model),
        ),
        migrations.AddConstraint(
            model_name='templatestarter',
            constraint=models.UniqueConstraint(condition=models.Q(is_deleted=False), fields=('template', 'api_name'), name='processes_template_starter_template_api_name_unique'),
        ),
    ]