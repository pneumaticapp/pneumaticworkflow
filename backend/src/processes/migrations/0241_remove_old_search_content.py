from django.db import migrations
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    """ Fills the user field in predicate and predicatetemplate
        models based on the Value field, which contains user.id,
        for entries with Field_type = 'User' """
    dependencies = [
        ('processes', '0240_populate_user_group_predicates'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldtemplate',
            name='account',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='accounts.Account'
            ),
        ),
        migrations.AddField(
            model_name='taskfield',
            name='account',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='accounts.Account'
            ),
        ),
        migrations.RunSQL(sql="""
          UPDATE processes_fieldtemplate main SET account_id = result.account_id
            FROM (
              SELECT pft.id, t.account_id
                FROM processes_fieldtemplate pft 
                  INNER JOIN processes_template t ON t.id = pft.template_id
            ) result
          WHERE main.id = result.id
        """),
        migrations.RunSQL(sql="""
          UPDATE processes_taskfield main SET account_id = result.account_id
            FROM (
              SELECT ptf.id, pw.account_id
                FROM processes_taskfield ptf 
                  INNER JOIN processes_workflow pw ON pw.id = ptf.workflow_id
            ) result
          WHERE main.id = result.id
        """),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS update_process_workflow_search_content ON processes_workflow"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS workflow_ins ON processes_workflow"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS workflow_insert ON processes_workflow"),

        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS update_process_fileattachment_search_content ON processes_fileattachment"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS fileattachment_ins ON processes_fileattachment"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS processes_fileattachment_ins ON processes_fileattachment"),

        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS processes_workflowevent_ins ON processes_workflowevent"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS update_process_workflowevent_search_content ON processes_workflowevent"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS workflow_insert ON processes_workflowevent"),

        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS kickoffvalue_ins ON processes_kickoffvalue"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS update_processes_kickoffvalue_search_content ON processes_kickoffvalue"),

        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS update_processes_task_search_content ON processes_task"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS task_insert ON processes_task"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS tasks_ins ON processes_task"),

        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS update_processes_taskfield_search_content ON processes_taskfield"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS taskfield_ins ON processes_taskfield"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS workflow_ins ON processes_taskfield"),

        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS tasktemplate_ins ON processes_tasktemplate"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS templates_ins ON processes_template"),

        migrations.RemoveField(
            model_name='fileattachment',
            name='search_content',
        ),
        migrations.RemoveField(
            model_name='kickoffvalue',
            name='search_content',
        ),
        migrations.RemoveField(
            model_name='task',
            name='search_content',
        ),
        migrations.RemoveField(
            model_name='taskfield',
            name='search_content',
        ),
        migrations.RemoveField(
            model_name='tasktemplate',
            name='search_content',
        ),
        migrations.RemoveField(
            model_name='template',
            name='search_content',
        ),
        migrations.RemoveField(
            model_name='workflow',
            name='search_content',
        ),
        migrations.RemoveField(
            model_name='workflowevent',
            name='search_content',
        ),
    ]
