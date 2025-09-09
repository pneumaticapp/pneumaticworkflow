from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0207_workflow_ancestor_task'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                UPDATE processes_workflow SET is_deleted=TRUE
                WHERE status=2
            """,
            reverse_sql=""
        )
    ]
