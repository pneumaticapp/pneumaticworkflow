# Generated by Django 2.2 on 2023-12-25 21:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0195_workflowevent_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='contains_comments',
            field=models.BooleanField(default=False),
        ),
        migrations.RunSQL("""
        UPDATE processes_task
        SET contains_comments = TRUE 
        FROM (
            SELECT DISTINCT(task_id)
            FROM processes_workflowevent
            WHERE is_deleted IS FALSE AND type = 5
        ) comments
        WHERE comments.task_id = processes_task.id
        """)
    ]
