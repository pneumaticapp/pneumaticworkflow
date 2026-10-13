from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0252_add_manager_performer_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='predicate',
            name='operator',
            field=models.CharField(
                choices=[('equals', 'Equal'), ('not_equals', 'Not equal'),
                         ('exists', 'Exists'), ('not_exists', 'Not exists'),
                         ('contains', 'Contains'),
                         ('not_contains', 'Not contains'),
                         ('more_than', 'More than'),
                         ('less_than', 'Less than'),
                         ('completed', 'completed'), ('skipped', 'skipped'),
                         ('completed_or_skipped', 'completed_or_skipped')],
                max_length=30),
        ),
        migrations.AlterField(
            model_name='predicatetemplate',
            name='operator',
            field=models.CharField(
                choices=[('equals', 'Equal'), ('not_equals', 'Not equal'),
                         ('exists', 'Exists'), ('not_exists', 'Not exists'),
                         ('contains', 'Contains'),
                         ('not_contains', 'Not contains'),
                         ('more_than', 'More than'),
                         ('less_than', 'Less than'),
                         ('completed', 'completed'), ('skipped', 'skipped'),
                         ('completed_or_skipped', 'completed_or_skipped')],
                max_length=30),
        ),
        migrations.RunSQL("""
            UPDATE processes_predicate p
            SET    operator = 'completed_or_skipped'
            FROM   processes_rule r
            WHERE  p.rule_id    = r.id
              AND  p.operator   = 'completed'
              AND  p.field_type = 'task'
        """),
            migrations.RunSQL("""
            UPDATE processes_predicatetemplate pt
            SET    operator = 'completed_or_skipped'
            FROM   processes_ruletemplate rt
            WHERE  pt.rule_id   = rt.id
              AND  pt.operator  = 'completed'
              AND  pt.field_type = 'task'
        """),
        migrations.RunSQL("""
            UPDATE processes_templatedraft td
            SET draft = (
                SELECT jsonb_set(
                    td.draft,
                    '{tasks}',
                    COALESCE(
                        jsonb_agg(
                            CASE
                                WHEN jsonb_typeof(task->'conditions') = 'array' THEN
                                    jsonb_set(
                                        task,
                                        '{conditions}',
                                        COALESCE(
                                            (
                                                SELECT jsonb_agg(
                                                    CASE
                                                        WHEN jsonb_typeof(cond->'rules') = 'array' THEN
                                                            jsonb_set(
                                                                cond,
                                                                '{rules}',
                                                                COALESCE(
                                                                    (
                                                                        SELECT jsonb_agg(
                                                                            CASE
                                                                                WHEN jsonb_typeof(rule->'predicates') = 'array' THEN
                                                                                    jsonb_set(
                                                                                        rule,
                                                                                        '{predicates}',
                                                                                        COALESCE(
                                                                                            (
                                                                                                SELECT jsonb_agg(
                                                                                                    CASE
                                                                                                        WHEN (pred->>'operator') = 'completed'
                                                                                                         AND (pred->>'field_type') = 'task'
                                                                                                        THEN jsonb_set(pred, '{operator}', '"completed_or_skipped"')
                                                                                                        ELSE pred
                                                                                                    END
                                                                                                )
                                                                                                FROM jsonb_array_elements(rule->'predicates') AS pred
                                                                                            ),
                                                                                            '[]'::jsonb
                                                                                        )
                                                                                    )
                                                                                ELSE rule
                                                                            END
                                                                        )
                                                                        FROM jsonb_array_elements(cond->'rules') AS rule
                                                                    ),
                                                                    '[]'::jsonb
                                                                )
                                                            )
                                                        ELSE cond
                                                    END
                                                )
                                                FROM jsonb_array_elements(task->'conditions') AS cond
                                            ),
                                            '[]'::jsonb
                                        )
                                    )
                                ELSE task
                            END
                        ),
                        '[]'::jsonb
                    )
                )
                FROM jsonb_array_elements(td.draft->'tasks') AS task
            )
            WHERE td.is_deleted = FALSE
              AND td.draft IS NOT NULL
              AND jsonb_typeof(td.draft->'tasks') = 'array'
              AND EXISTS (
                  SELECT 1
                  FROM jsonb_array_elements(td.draft->'tasks') AS task,
                       jsonb_array_elements(task->'conditions') AS cond,
                       jsonb_array_elements(cond->'rules') AS rule,
                       jsonb_array_elements(rule->'predicates') AS pred
                  WHERE (pred->>'operator') = 'completed'
                    AND (pred->>'field_type') = 'task'
              )
        """)
    ]
