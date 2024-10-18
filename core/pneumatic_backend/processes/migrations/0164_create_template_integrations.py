from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0163_auto_20220914_0919'),
        ('webhooks', '0004_auto_20200824_1922'),
    ]

    operations = [
        migrations.RunSQL("""
        INSERT INTO processes_templateintegrations (
          template_id,
          account_id,
          webhooks,
          shared,
          api,
          zapier,
          is_deleted
        )
        SELECT
         pt.id AS template_id,
         pt.account_id,
         CASE
          WHEN COUNT(w.id) > 0 THEN TRUE
          ELSE FALSE
         END AS webhooks,
         FALSE AS shared,
         FALSE AS api,
         FALSE AS zapier,
         FALSE AS is_deleted
        FROM processes_template pt
         LEFT JOIN webhooks_webhook w
          ON pt.account_id = w.account_id
            AND w.is_deleted IS FALSE
            AND w.target IS NOT NULL
        
        WHERE pt.is_deleted IS FALSE
        GROUP BY pt.id
        ORDER BY pt.account_id
      ON CONFLICT DO NOTHING
    """),
    ]
