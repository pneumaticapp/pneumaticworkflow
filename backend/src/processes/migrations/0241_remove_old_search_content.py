from django.db import migrations


class Migration(migrations.Migration):
    """ Fills the user field in predicate and predicatetemplate
        models based on the Value field, which contains user.id,
        for entries with Field_type = 'User' """
    dependencies = [
        ('processes', '0240_populate_user_group_predicates'),
    ]

    operations = [
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS update_process_fileattachment_search_content ON processes_fileattachment"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS update_process_workflow_search_content ON processes_workflow"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS update_process_workflowevent_search_content ON processes_workflowevent"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS update_processes_kickoffvalue_search_content ON processes_kickoffvalue"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS update_processes_task_search_content ON processes_task"),
        migrations.RunSQL(sql="DROP TRIGGER IF EXISTS update_processes_taskfield_search_content ON processes_taskfield"),
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
