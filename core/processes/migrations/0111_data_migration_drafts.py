from django.db import migrations


def forwards(apps, schema_editor):
    pass


def backwards(*args, **kwards):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0110_condition_conditiontemplate_predicate_predicatetemplate_rule_ruletemplate'),
    ]

    operations = [
        migrations.RunPython(
            code=forwards,
            reverse_code=backwards,
            atomic=True
        )
    ]
