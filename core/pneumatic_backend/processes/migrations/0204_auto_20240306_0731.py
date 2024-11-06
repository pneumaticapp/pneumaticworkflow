from django.db import migrations


def set_public_id(*args, **options):

    from pneumatic_backend.processes.models.templates.template import (
        Template,
        get_new_embed_id,
        get_new_public_id
    )

    for template in Template.objects.filter(public_id=None, embed_id=None):
        template.public_id = get_new_public_id()
        template.embed_id = get_new_embed_id()
        template.save(update_fields=['public_id', 'embed_id'])

    for template in Template.objects.filter(public_id=None):
        template.public_id = get_new_public_id()
        template.save(update_fields=['public_id'])

    for template in Template.objects.filter(embed_id=None):
        template.embed_id = get_new_embed_id()
        template.save(update_fields=['embed_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0116_auto_20240306_0731'),
        ('processes', '0203_auto_20240226_0915'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fileattachment',
            name='comment',
        ),
        migrations.RemoveField(
            model_name='workflowevent',
            name='old_comment_id',
        ),
        migrations.RemoveField(
            model_name='workflowevent',
            name='old_id',
        ),
        migrations.DeleteModel(
            name='Comment',
        ),
        migrations.RunPython(
            code=set_public_id,
            reverse_code=migrations.RunPython.noop
        ),
        migrations.RunSQL(
            sql="""
                UPDATE processes_template
                SET 
                  public_id = substr(md5(random()::text), 1, 8)
                WHERE
                  public_id IS NULL 
                  AND is_deleted IS TRUE
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                UPDATE processes_template
                SET 
                  embed_id = substr(md5(random()::text), 1, 32)
                WHERE
                  embed_id IS NULL 
                  AND is_deleted IS TRUE
            """,
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
