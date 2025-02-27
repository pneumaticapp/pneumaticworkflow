# Generated by Django 2.2.17 on 2021-06-03 13:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0132_auto_20210524_1059'),
    ]

    operations = [
        migrations.AddField(
            model_name='conditiontemplate',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='conditions', to='processes.Template'),
        ),
        migrations.AddField(
            model_name='fieldtemplate',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='processes.Template'),
        ),
        migrations.AddField(
            model_name='fieldtemplateselection',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='selections', to='processes.Template'),
        ),
        migrations.AddField(
            model_name='predicatetemplate',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='predicates', to='processes.Template'),
        ),
        migrations.AddField(
            model_name='ruletemplate',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='processes.Template'),
        ),
    ]
