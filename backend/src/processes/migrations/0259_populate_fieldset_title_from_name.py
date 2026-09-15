from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0258_rebuild_attachment_permissions'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                UPDATE processes_fieldset
                SET title = name;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                UPDATE processes_fieldsettemplate
                SET title = name;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

    ]
