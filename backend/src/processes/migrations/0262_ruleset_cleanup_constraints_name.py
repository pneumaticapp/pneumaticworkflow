from django.db import migrations, models


# 0260 copied every FieldsetTemplateRule into the new ruleset tables, including
# soft-deleted ones, and wrote the old rule kind straight into
# GroupAnd.operator even though the two vocabularies only share 'sum_equal'.
# Every row in these tables at this point comes from that data step, so the
# leftovers can be dropped by value.
SUM_OPERATORS = ('sum_equal', 'sum_greater_than', 'sum_less_than')


def cleanup_migrated_fieldset_rules(apps, schema_editor):
    RuleSet = apps.get_model('processes', 'FieldSetTemplateRuleSet')
    GroupAnd = apps.get_model('processes', 'FieldSetTemplateRuleGroupAnd')

    ruleset_ids = set(
        RuleSet.objects
        .filter(is_deleted=True)
        .values_list('id', flat=True)
    )
    ruleset_ids.update(
        GroupAnd.objects
        .exclude(operator__in=SUM_OPERATORS)
        .values_list('group_or__fieldset_rule_id', flat=True)
    )
    if ruleset_ids:
        RuleSet.objects.filter(id__in=ruleset_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0261_fieldtemplateruleset_name'),
    ]

    operations = [
        migrations.RunPython(
            cleanup_migrated_fieldset_rules,
            migrations.RunPython.noop,
            elidable=True,
        ),
        migrations.AlterField(
            model_name='fieldrulegroupand',
            name='operator',
            field=models.CharField(choices=[('equal', 'Equal'), ('not_equals', 'Not equal'), ('exists', 'Exists'), ('not_exists', 'Not exists'), ('greater_than', 'Greater than'), ('less_than', 'Less than'), ('contains', 'Contains'), ('not_contains', 'Not contains')], max_length=50),
        ),
        migrations.AlterField(
            model_name='fieldtemplaterulegroupand',
            name='operator',
            field=models.CharField(choices=[('equal', 'Equal'), ('not_equals', 'Not equal'), ('exists', 'Exists'), ('not_exists', 'Not exists'), ('greater_than', 'Greater than'), ('less_than', 'Less than'), ('contains', 'Contains'), ('not_contains', 'Not contains')], max_length=50),
        ),
        migrations.AddConstraint(
            model_name='fieldsettemplaterulegroupand',
            constraint=models.UniqueConstraint(condition=models.Q(('is_deleted', False), ('template__isnull', True)), fields=('group_or', 'api_name', 'account'), name='fieldset_rulegroupand_shared_api_name_unique'),
        ),
        migrations.AddConstraint(
            model_name='fieldsettemplaterulegroupor',
            constraint=models.UniqueConstraint(condition=models.Q(('is_deleted', False), ('template__isnull', True)), fields=('fieldset_rule', 'api_name', 'account'), name='fieldset_rulegroupor_shared_api_name_unique'),
        ),
        migrations.AddConstraint(
            model_name='fieldsettemplateruleset',
            constraint=models.UniqueConstraint(condition=models.Q(('is_deleted', False), ('template__isnull', True)), fields=('fieldset', 'api_name', 'account'), name='fieldsetruleset_shared_api_name_unique'),
        ),
        migrations.AddConstraint(
            model_name='fieldtemplaterulegroupand',
            constraint=models.UniqueConstraint(condition=models.Q(('is_deleted', False), ('template__isnull', True)), fields=('group_or', 'api_name', 'account'), name='rulegroupand_shared_api_name_unique'),
        ),
        migrations.AddConstraint(
            model_name='fieldtemplaterulegroupor',
            constraint=models.UniqueConstraint(condition=models.Q(('is_deleted', False), ('template__isnull', True)), fields=('ruleset', 'api_name', 'account'), name='rulegroupor_shared_api_name_unique'),
        ),
        migrations.AddConstraint(
            model_name='fieldtemplateruleset',
            constraint=models.UniqueConstraint(condition=models.Q(('is_deleted', False), ('template__isnull', True)), fields=('field', 'api_name', 'account'), name='fieldtemplateruleset_shared_api_name_unique'),
        ),
        migrations.AddField(
            model_name='fieldruleset',
            name='name',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
