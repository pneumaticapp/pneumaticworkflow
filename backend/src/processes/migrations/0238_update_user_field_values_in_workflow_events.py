from django.db import migrations


class Migration(migrations.Migration):
    """
    Restore the value in the Value field for fields of the type "user" in
    Task_json-> Output-> Value, now the user name is stored there
    according to the logic of the user.name_by_BY_STATUS method.
    """
    dependencies = [
        ('processes', '0237_auto_20250916_2245'),
    ]

    operations = [
        migrations.RunSQL(
            """
            UPDATE processes_workflowevent 
            SET task_json = jsonb_set(
              task_json, 
              '{output}', 
              (
                SELECT jsonb_agg(
                  CASE 
                    WHEN field->>'type' = 'user' THEN
                      jsonb_set(
                        field,
                       '{value}',
                        to_jsonb(
                          CASE 
                            WHEN field->>'value' ~ '^[0-9]+$'
                              AND u.id IS NOT NULL
                              AND u.is_deleted = false
                              AND u.status = 'active'
                              AND u.type = 'user'
                            THEN TRIM(CONCAT(u.first_name, ' ', u.last_name))
                            WHEN field->>'value' ~ '^[0-9]+$'
                              AND u.id IS NOT NULL
                              AND u.is_deleted = false
                              AND u.status = 'invited'
                              AND u.type = 'user'
                            THEN u.email || ' (invited user)'
                            ELSE ''
                          END
                        )
                      )
                    ELSE field
                END
              )
              FROM jsonb_array_elements(task_json->'output') AS field
              LEFT JOIN accounts_user u 
                ON field->>'type' = 'user'
                AND CASE
                  WHEN field->>'value' ~ '^[0-9]+$'
                  THEN u.id = (field->>'value')::INTEGER
                  ELSE FALSE
                END
              )
            )
            WHERE task_json ? 'output' 
              AND jsonb_typeof(task_json->'output') = 'array'
              AND EXISTS (
                SELECT 1 
                FROM jsonb_array_elements(task_json->'output') AS field
                WHERE field->>'type' = 'user' 
              );
            """
        )
    ]
