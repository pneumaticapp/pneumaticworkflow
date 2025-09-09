from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0229_auto_20250404_1333'),
    ]

    operations = [
        migrations.AddField(
            model_name='fileattachment',
            name='access_type',
            field=models.CharField(
                choices=[('account', 'account'), ('restricted', 'restricted')],
                default='restricted',
                max_length=20
            ),
            preserve_default=True,
        ),
        
        migrations.CreateModel(
            name='FileAttachmentPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
                ('attachment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permissions', to='processes.FileAttachment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='file_permissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'attachment')},
            },
        ),
    ]