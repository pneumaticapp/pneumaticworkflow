from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '__latest__'),
        ('auth', '__latest__'),
        ('contenttypes', '__latest__'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupObjectPermission',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'object_pk',
                    models.CharField(max_length=255),
                ),
                (
                    'content_type',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='contenttypes.ContentType',
                    ),
                ),
                (
                    'permission',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='auth.Permission',
                    ),
                ),
                (
                    'group',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='accounts.UserGroup',
                    ),
                ),
            ],
            options={
                'unique_together': {('group', 'permission', 'object_pk')},
                'indexes': [
                    models.Index(
                        fields=[
                            'group',
                            'permission',
                            'content_type',
                            'object_pk',
                        ],
                        name='permissions_group_perm_ct_obj_idx',
                    ),
                    models.Index(
                        fields=['group', 'content_type', 'object_pk'],
                        name='permissions_group_ct_obj_idx',
                    ),
                ],
            },
        ),
    ]
