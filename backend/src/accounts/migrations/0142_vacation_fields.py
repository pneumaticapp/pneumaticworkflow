from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0141_notification_text_default'),
    ]

    operations = [
        # UserGroup.type
        migrations.AddField(
            model_name='usergroup',
            name='type',
            field=models.CharField(
                choices=[
                    ('regular', 'Regular'),
                    ('personal', 'Personal'),
                ],
                default='regular',
                max_length=20,
            ),
        ),
        # UserVacation model (normalized vacation data)
        migrations.CreateModel(
            name='UserVacation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.account')),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('absence_status', models.CharField(choices=[('active', 'Active'), ('vacation', 'On vacation'), ('sick_leave', 'Sick leave')], default='vacation', max_length=20)),
                ('substitute_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vacation_owners', to='accounts.usergroup')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='vacation', to='accounts.user')),
            ],
        ),
    ]
