# Generated by Django 2.2.12 on 2020-05-15 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0029_merge_20200512_1241'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kickofffieldtemplate',
            name='type',
            field=models.CharField(choices=[('string', 'String'), ('text', 'Text')], max_length=10),
        ),
        migrations.AlterField(
            model_name='taskfield',
            name='type',
            field=models.CharField(choices=[('string', 'String'), ('text', 'Text')], max_length=10),
        ),
        migrations.AlterField(
            model_name='taskfieldtemplate',
            name='type',
            field=models.CharField(choices=[('string', 'String'), ('text', 'Text')], max_length=10),
        ),
    ]
