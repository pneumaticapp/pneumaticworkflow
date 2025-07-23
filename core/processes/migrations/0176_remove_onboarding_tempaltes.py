from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0175_disable_urgent_for_done_wf'),
    ]

    operations = [
        migrations.RunSQL("""
            UPDATE processes_template
            SET is_deleted = TRUE
            WHERE type IN (
               'builtin_admin_onboarding',
               'builtin_user_onboarding',
               'builtin_account_owner_onboarding'
            )
        """)
    ]
