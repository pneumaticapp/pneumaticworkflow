# Generated by Django 2.2.28 on 2023-03-22 18:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0183_remove_rawduedate_template_id'),
    ]

    operations = [
        migrations.RunSQL("""
            INSERT INTO processes_rawduedatetemplate (
                is_deleted,
                api_name,
                duration,
                rule,
                source_id,
                task_id,
                template_id
            ) SELECT
                FALSE,
                'raw-due-date-' || upper(substr(md5(random()::text), 0, 10)),
                due_in,
                'after task started',
                api_name,
                id,
                template_id
            FROM processes_tasktemplate
            WHERE due_in IS NOT NULL
              AND is_deleted is FALSE
        """),
        migrations.RunSQL("""
            INSERT INTO processes_rawduedate (
                is_deleted,
                api_name,
                duration,
                rule,
                source_id,
                task_id
            ) SELECT
                FALSE,
                dd.api_name,
                pt.due_in,
                'after task started',
                pt.api_name,
                pt.id
            FROM processes_rawduedatetemplate dd
              INNER JOIN processes_task pt ON dd.task_id = pt.template_id
            WHERE pt.is_deleted IS FALSE
              AND pt.due_in IS NOT NULL
        """),
        migrations.RunSQL("""
            UPDATE processes_task SET due_date = date_first_started + due_in
            WHERE due_in IS NOT NULL
                AND date_first_started IS NOT NULL
                AND is_deleted IS FALSE
        """)
    ]
