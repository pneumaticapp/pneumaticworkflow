# Generated by Django 2.2.12 on 2020-05-05 22:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0022_auto_20200505_2159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kickofffieldtemplate',
            name='workflow',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='kickoff', to='processes.Workflow'),
        ),
    ]
