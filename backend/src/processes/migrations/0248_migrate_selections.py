from django.db import migrations


def migrate_drafts(apps, schema_editor):

    """
        Update template draft,
        replace selection api_name to selection value in the predicates
    """

    predicates_sql = """
    -- SQL returns all predicates for update "value"
    -- from selection "api_name" to selection "value"

    SELECT
        ptd.draft_id,
        ptd.template_name,
        ptd.account_name,
        all_selections.selection->>'api_name'      AS selection_api_name,
        filtered_predicates.predicate->>'api_name' AS predicate_api_name,
        all_selections.selection->>'value'         AS selection_value
    FROM (
        -- Get drafts with selections in the predicates for active accounts
        SELECT DISTINCT ON (td.id)
            td.id AS draft_id,
            pt.account_id,
            pt.name AS template_name,
            pt.id AS template_id,
            acc.name AS account_name,
            acc.billing_plan
        FROM processes_templatedraft td
        JOIN processes_template pt
            ON td.template_id = pt.id
        JOIN accounts_account acc
            ON pt.account_id = acc.id
        JOIN LATERAL jsonb_path_query(
            td.draft,
            '$.tasks[*].conditions[*].rules[*].predicates[*]'
        ) AS predicate ON (
            predicate->>'field_type' IN ('radio', 'checkbox', 'dropdown')
            AND predicate->>'operator' NOT IN ('not_exists', 'exists')
        )
        WHERE
            td.is_deleted = FALSE
            AND pt.is_active = FALSE
            AND pt.is_deleted = FALSE
            AND (
                acc.plan_expiration > NOW()
                AND acc.billing_plan != 'free'
            )
        ) ptd
    LEFT JOIN (
         -- Get selections из task and kickoff fields
        SELECT selection, td.id AS draft_id
        FROM processes_templatedraft td
        JOIN LATERAL jsonb_path_query(td.draft, '$.kickoff.fields[*].selections[*]') AS selection ON true
        UNION ALL
        SELECT selection, td.id AS draft_id
        FROM processes_templatedraft td
        JOIN LATERAL jsonb_path_query(td.draft, '$.tasks[*].fields[*].selections[*]') AS selection ON true
    ) all_selections ON all_selections.draft_id = ptd.draft_id
    INNER JOIN (
         -- Get predicates with selections 
        SELECT predicate, td.id AS draft_id
        FROM processes_templatedraft td
        JOIN LATERAL jsonb_path_query(
            td.draft,
            '$.tasks[*].conditions[*].rules[*].predicates[*]'
        ) AS predicate ON true
        WHERE predicate->>'field_type' IN ('radio', 'checkbox', 'dropdown')
          AND predicate->>'operator' NOT IN ('not_exists', 'exists')
    ) filtered_predicates ON all_selections.selection->>'api_name' = filtered_predicates.predicate->>'value' 
        AND filtered_predicates.draft_id = ptd.draft_id
    ORDER BY ptd.account_name
    """

    def _get_updated_draft(
        draft: dict,
        selection_value: str,
        selection_api_name: str,
        predicate_api_name: str,
        draft_id: int,
        template_name: str,
        account_name: str,
    ) -> dict:
        for task in draft.get("tasks", []):
            for condition in task.get("conditions", []):
                for rule in condition.get("rules", []):
                    for predicate in rule.get("predicates", []):
                        if predicate.get("api_name") == predicate_api_name:
                            if predicate.get("value") == selection_api_name:
                                predicate["value"] = selection_value
                                print(
                                    f'Draft updated: {draft_id}, '
                                    f'Template name: "{template_name}" '
                                    f'predicate_api_name: "{predicate_api_name}"'
                                )
                                return draft
        print(
            f'Draft predicate not updated: '
            f'Account: "{account_name}", '
            f'Template: "{template_name}",'
            f'draft_id: "{draft_id}", '
            f'predicate_api_name: "{predicate_api_name}", '
            f'selection_api_name: "{selection_api_name}", '
            f'selection_value: "{selection_value}"'
        )
        return draft

    TemplateDraft = apps.get_model('processes', 'TemplateDraft')
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute(predicates_sql, [])
        rows = cursor.fetchall()
        for row in rows:
            draft_id = row[0]
            template_draft = TemplateDraft.objects.get(id=draft_id)
            template_draft.draft = _get_updated_draft(
                draft=template_draft.draft,
                selection_value=row[5],
                selection_api_name=row[3],
                predicate_api_name=row[4],
                draft_id=draft_id,
                template_name=row[1],
                account_name=row[2],
            )
            template_draft.save(update_fields=("draft",))

class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0247_add_datasets'),
    ]

    operations = [
        migrations.RunSQL("""
            -- Replace selection api_name with the selection value
            -- in the template conditions
            
            WITH ranked AS (
                SELECT DISTINCT pt.id AS predicate_id, fts.value
                FROM processes_predicatetemplate pt
                INNER JOIN processes_fieldtemplate ft 
                    ON ft.api_name = pt.field
                INNER JOIN processes_fieldtemplateselection fts 
                    ON fts.field_template_id = ft.id
                WHERE ft.is_deleted IS FALSE
                  AND fts.is_deleted IS FALSE
                  AND pt.is_deleted IS FALSE
                  AND ft.template_id = pt.template_id
                  AND fts.api_name = pt.value
                  AND pt.field_type IN ('radio', 'checkbox', 'dropdown')
                  AND pt.operator NOT IN ('not_exists', 'exists')
                ORDER BY pt.id DESC
            )
            UPDATE processes_predicatetemplate pt
            SET value = ranked.value
            FROM ranked
            WHERE pt.id = ranked.predicate_id
        """),
        migrations.RunSQL("""
            -- Replace selection api_name with the selection value 
            -- in the conditions

            WITH ranked AS (
                SELECT
                    pp.id AS predicate_id,
                    fs.value
                FROM processes_predicate pp
                    INNER JOIN processes_rule r
                        ON r.id = pp.rule_id
                    INNER JOIN processes_condition c
                        ON c.id = r.condition_id
                    INNER JOIN processes_task t
                        ON t.id = c.task_id
                    INNER JOIN processes_taskfield tf
                        ON tf.api_name = pp.field
                    INNER JOIN processes_fieldselection fs
                        ON fs.field_id = tf.id
                WHERE fs.is_deleted IS FALSE
                  AND pp.is_deleted IS FALSE
                  AND tf.is_deleted IS FALSE
                  AND fs.api_name = pp.value
                  AND tf.workflow_id = t.workflow_id
                  AND pp.field_type IN ('radio', 'checkbox', 'dropdown')
                  AND pp.operator NOT IN ('not_exists', 'exists')
            )
            UPDATE processes_predicate pp
            SET value = ranked.value
            FROM ranked
            WHERE pp.id = ranked.predicate_id
        """),
        migrations.RunPython(
            code=migrate_drafts,
            reverse_code=migrations.RunPython.noop
        ),
        migrations.RunSQL("""
            -- Delete duplicates from a processes_fieldtemplateselection
            WITH duplicates AS (
                SELECT
                    s.id,
                    ROW_NUMBER() OVER (
                        PARTITION BY s.field_template_id, s.value
                        ORDER BY s.id
                    ) AS rn
                FROM processes_fieldtemplateselection s
                INNER JOIN processes_template t ON t.id = s.template_id
                INNER JOIN accounts_account a ON a.id = t.account_id
                WHERE s.is_deleted = false
            )
            DELETE FROM processes_fieldtemplateselection
            WHERE id IN (SELECT id FROM duplicates WHERE rn > 1)
        """),
        migrations.RunSQL("""
            -- Delete all duplicates from a processes_fieldselection
            WITH duplicates AS (
                SELECT
                    s.id,
                    ROW_NUMBER() OVER (
                        PARTITION BY s.field_id, s.value
                        ORDER BY s.id
                    ) AS rn
                FROM processes_fieldselection s
                INNER JOIN processes_taskfield tf ON tf.id = s.field_id
                INNER JOIN accounts_account a ON a.id = tf.account_id
                WHERE s.is_deleted = false
            )
            DELETE FROM processes_fieldselection
            WHERE id IN (SELECT id FROM duplicates WHERE rn > 1)
        """)
    ]
