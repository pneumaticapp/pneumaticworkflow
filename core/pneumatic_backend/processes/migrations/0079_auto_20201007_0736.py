# Generated by Django 2.2.16 on 2020-10-07 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0078_auto_20201005_1231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fieldtemplate',
            name='type',
            field=models.CharField(choices=[('string', 'String'), ('text', 'Text'), ('radio', 'Radio'), ('checkbox', 'Checkbox'), ('date', 'Date'), ('url', 'Url'), ('dropdown', 'Dropdown'), ('file', 'File')], max_length=10),
        ),
        migrations.AlterField(
            model_name='taskfield',
            name='type',
            field=models.CharField(choices=[('string', 'String'), ('text', 'Text'), ('radio', 'Radio'), ('checkbox', 'Checkbox'), ('date', 'Date'), ('url', 'Url'), ('dropdown', 'Dropdown'), ('file', 'File')], max_length=10),
        ),
    ]