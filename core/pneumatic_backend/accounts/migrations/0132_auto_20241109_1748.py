import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0131_add_bucket_name'),
        ('processes', '0229_auto_20250404_1333'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='workflow_json',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='task_json',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.RunSQL("""
            UPDATE accounts_notification an
            SET
                workflow_json = CASE 
                    WHEN an.type = 'system' THEN NULL
                    ELSE jsonb_build_object(
                        'id', pw.id,
                        'name', pw.name
                    )
                END,
                task_json = CASE 
                    WHEN an.type = 'system' THEN NULL
                    WHEN an.type = 'delay_workflow' THEN jsonb_build_object(
                        'id', pt.id,
                        'name', pt.name,
                        'delay', (
                            SELECT jsonb_build_object(
                                'estimated_end_date_tsp', EXTRACT(EPOCH FROM pd.estimated_end_date),
                                'duration', pd.duration
                            )
                            FROM processes_delay pd
                            WHERE pd.task_id = pt.id
                            AND pd.is_deleted = FALSE
                            AND pd.end_date IS NULL
                            ORDER BY pd.id DESC
                            LIMIT 1
                        )
                    )
                    WHEN an.type = 'due_date_changed' THEN jsonb_build_object(
                        'id', pt.id,
                        'name', pt.name,
                        'due_date_tsp', EXTRACT(EPOCH FROM pt.due_date)
                    )
                    ELSE jsonb_build_object(
                        'id', pt.id,
                        'name', pt.name
                    )
                END
            FROM processes_task pt
            LEFT JOIN processes_workflow pw ON pt.workflow_id = pw.id
            WHERE an.task_id = pt.id
            AND an.workflow_json IS NULL
            AND an.task_json IS NULL
            AND an.task_id IS NOT NULL;
        """),
        migrations.AlterField(
            model_name='notification',
            name='task',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='processes.Task',
            ),
        ),
    ]
