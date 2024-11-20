from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0216_auto_20241016_0020'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='template',
            name='performers_count',
        ),
        migrations.RemoveField(
            model_name='template',
            name='tasks_count',
        ),
        migrations.RunSQL(
            """
            UPDATE processes_systemtemplate
            SET template = template - 'performers_count' - 'tasks_count'
            WHERE template IS NOT NULL;
            """,
        )
    ]

