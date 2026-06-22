from django.db import migrations


class Migration(migrations.Migration):
    """
    Renames FieldsetTemplateRule -> FieldsetTemplateRuleOld (deprecated model).
    The db_table is pinned via Meta.db_table = 'processes_fieldsettemplate_rule',
    so the actual database table is NOT renamed — only the Django model label
    and ContentType record change.
    """

    dependencies = [
        ('processes', '0254_auto_20260609_1910'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='FieldsetTemplateRule',
            new_name='FieldsetTemplateRuleOld',
        ),
        migrations.AlterModelTable(
            name='FieldsetTemplateRuleOld',
            table='processes_fieldsettemplate_rule_old',
        ),
    ]
