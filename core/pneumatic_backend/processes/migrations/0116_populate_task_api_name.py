from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0115_auto_20210408_1140'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
              UPDATE processes_taskworkflow tw SET api_name = collection.api_name
                FROM (
                  SELECT id, concat('task-', substr(md5(random()::text), 0, 6)) as api_name
                    FROM processes_taskworkflow
                ) collection
              WHERE tw.id = collection.id
            """,
            reverse_sql="""UPDATE processes_taskworkflow SET api_name = NULL""",
        )
    ]
