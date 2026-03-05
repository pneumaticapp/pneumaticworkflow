from django.db import migrations, models


def backfill_is_hidden_in_template_versions(apps, schema_editor):
    TemplateVersion = apps.get_model('processes', 'TemplateVersion')
    for tv in TemplateVersion.objects.all().iterator():
        changed = False
        data = tv.data
        kickoff = data.get('kickoff')
        if kickoff:
            for field in kickoff.get('fields') or []:
                if 'is_hidden' not in field:
                    field['is_hidden'] = False
                    changed = True
        for task in data.get('tasks') or []:
            for field in task.get('fields') or []:
                if 'is_hidden' not in field:
                    field['is_hidden'] = False
                    changed = True
        if changed:
            tv.data = data
            tv.save(update_fields=['data'])


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0242_add_new_search_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldtemplate',
            name='is_hidden',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='taskfield',
            name='is_hidden',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            backfill_is_hidden_in_template_versions,
            migrations.RunPython.noop,
        ),
    ]
