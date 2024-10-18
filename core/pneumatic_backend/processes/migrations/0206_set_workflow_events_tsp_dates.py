from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0205_default_public_id'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                UPDATE processes_workflowevent
                SET task_json = (
                  jsonb_build_object(
                   'due_date_tsp',
                   EXTRACT(EPOCH FROM ((task_json->>'due_date')::timestamptz AT TIME ZONE 'UTC'))
                 ) || task_json
                )
                WHERE task_json->'due_date' != 'null'
            """,
            reverse_sql=""
        ),
        migrations.RunSQL(
            sql="""
                UPDATE processes_workflowevent
                SET task_json = (jsonb_build_object('due_date_tsp', null) || task_json)
                WHERE task_json->'due_date' = 'null'
            """,
            reverse_sql=""
        ),
        migrations.RunSQL(
            sql="""
                UPDATE processes_workflowevent
                SET watched = updated.watched
                FROM (
                  SELECT
                    we.id,
                    array_agg(wea.new_watched)::jsonb[] AS watched
                  FROM (
                      SELECT
                        event_id,
                        json_build_object(
                          'date_tsp', EXTRACT(EPOCH FROM (created AT TIME ZONE 'UTC')),
                          'user_id', user_id) AS new_watched
                      FROM processes_workfloweventaction
                    ) AS wea
                    JOIN processes_workflowevent we ON we.id = wea.event_id
                  GROUP BY we.id
                ) AS updated
                WHERE processes_workflowevent.id = updated.id
            """,
            reverse_sql=""
        ),
        migrations.RunSQL(
            sql="""
            UPDATE processes_workflowevent
            SET delay_json = (
              jsonb_build_object(
               'id', delay_json->>'id',
               'duration', delay_json->>'duration',
               'start_date', delay_json->>'start_date',
               'estimated_end_date', delay_json->>'estimated_end_date',
               'end_date', delay_json->>'end_date',
               'start_date_tsp', EXTRACT(EPOCH FROM ((delay_json->>'start_date')::timestamptz AT TIME ZONE 'UTC')),
               'estimated_end_date_tsp', EXTRACT(EPOCH FROM ((delay_json->>'estimated_end_date')::timestamptz AT TIME ZONE 'UTC')),
               'end_date_tsp', (
                 CASE
                   WHEN delay_json->'end_date' = 'null' THEN null
                   ELSE EXTRACT(EPOCH FROM ((delay_json->>'end_date')::timestamptz AT TIME ZONE 'UTC'))
                 END
               )
             )
            )
            WHERE delay_json != 'null' AND type in (7, 17)
            """
        )
    ]
