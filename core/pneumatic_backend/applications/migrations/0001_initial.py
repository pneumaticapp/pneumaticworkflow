# Generated by Django 2.2.7 on 2019-11-06 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Applications',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=16, verbose_name='Name of app')),
                ('image', models.URLField(blank=True, verbose_name='URL to image for this app')),
            ],
        ),
    ]
