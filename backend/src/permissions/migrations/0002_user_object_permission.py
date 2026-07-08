from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0011_update_proxy_permissions'),
        ('permissions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserObjectPermission',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                )),
                ('object_pk', models.CharField(
                    max_length=255,
                    verbose_name='object ID',
                )),
                ('source_type', models.CharField(
                    choices=[
                        ('Performer', 'Performer'),
                        ('PerformerGroup', 'Performer Group'),
                        ('Mention', 'Mention'),
                        ('TemplateOwner', 'Template Owner'),
                        ('WorkflowViewer', 'Workflow Viewer'),
                        ('Vacation', 'Vacation substitute'),
                    ],
                    help_text=(
                        'The model/entity that provided this permission.'
                    ),
                    max_length=50,
                )),
                ('source_id', models.CharField(
                    help_text='PK of the source entity.',
                    max_length=255,
                )),
                ('content_type', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='+',
                    to='contenttypes.ContentType',
                )),
                ('permission', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='+',
                    to='auth.Permission',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='object_permissions',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='userobjectpermission',
            index=models.Index(
                fields=['content_type', 'object_pk', 'user'],
                name='perm_uop_ct_obj_user_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='userobjectpermission',
            index=models.Index(
                fields=['source_type', 'source_id'],
                name='perm_uop_source_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='userobjectpermission',
            index=models.Index(
                fields=[
                    'content_type', 'object_pk',
                    'source_type', 'source_id',
                ],
                name='perm_uop_ct_obj_source_idx',
            ),
        ),
        migrations.AddConstraint(
            model_name='userobjectpermission',
            constraint=models.UniqueConstraint(
                fields=('user', 'permission', 'content_type', 'object_pk', 'source_type', 'source_id'),
                name='perm_uop_unique',
            ),
        ),
    ]
