# Generated by Django 2.2.26 on 2022-03-18 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0087_auto_20220302_0855'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='user',
            name='user_email_unique',
        ),
        migrations.RemoveConstraint(
            model_name='user',
            name='user_username_unique',
        ),
        migrations.AddField(
            model_name='user',
            name='type',
            field=models.CharField(choices=[('user', 'user'), ('guest', 'guest')], default='user', max_length=16),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(
                condition=models.Q(('is_deleted', False), ('type', 'guest'), models.Q(_negated=True, status='inactive')),
                fields=('email', 'account_id'),
                name='user_email_account_unique'
            ),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(
                condition=models.Q(('is_deleted', False), ('type', 'user'), models.Q(_negated=True, status='inactive')),
                fields=('email',),
                name='user_email_unique'
            ),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(
                condition=models.Q(('is_deleted', False), ('type', 'user'), models.Q(_negated=True, status='inactive')),
                fields=('username',),
                name='user_username_unique'
            ),
        ),
    ]
