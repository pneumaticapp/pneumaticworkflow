# Generated migration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '__latest__'),
        ('processes', '__latest__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'is_deleted',
                    models.BooleanField(default=False)
                ),
                (
                    'date_created',
                    models.DateTimeField(auto_now_add=True)
                ),
                (
                    'date_updated',
                    models.DateTimeField(auto_now=True)
                ),
                (
                    'file_id',
                    models.CharField(
                        help_text=(
                            'Unique file identifier in the file service'
                        ),
                        max_length=64,
                        unique=True
                    )
                ),
                (
                    'access_type',
                    models.CharField(
                        choices=[
                            ('public', 'Public'),
                            ('account', 'Account'),
                            ('restricted', 'Restricted')
                        ],
                        default='account',
                        help_text='File access type',
                        max_length=20
                    )
                ),
                (
                    'source_type',
                    models.CharField(
                        choices=[
                            ('Account', 'Account'),
                            ('Workflow', 'Workflow'),
                            ('Task', 'Task'),
                            ('Template', 'Template')
                        ],
                        help_text='File source type',
                        max_length=20
                    )
                ),
                (
                    'account',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='accounts.Account'
                    )
                ),
                (
                    'task',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='storage_attachments',
                        to='processes.Task'
                    )
                ),
                (
                    'template',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='storage_attachments',
                        to='processes.Template'
                    )
                ),
                (
                    'workflow',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='storage_attachments',
                        to='processes.Workflow'
                    )
                ),
            ],
            options={
                'permissions': (
                    ('view_attachment', 'Can view attachment'),
                ),
            },
        ),
        migrations.AddIndex(
            model_name='attachment',
            index=models.Index(
                fields=['file_id'],
                name='storage_att_file_id_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='attachment',
            index=models.Index(
                fields=['source_type', 'account'],
                name='storage_att_source_account_idx'
            ),
        ),
    ]

