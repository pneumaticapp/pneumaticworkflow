from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0260_auto_20260814_2003'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldtemplateruleset',
            name='name',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='fieldrulegroupor',
            old_name='field_rule',
            new_name='ruleset',
        ),
        migrations.RenameField(
            model_name='fieldtemplaterulegroupor',
            old_name='field_rule',
            new_name='ruleset',
        ),
        migrations.AlterField(
            model_name='fieldrulegroupand',
            name='operator',
            field=models.CharField(
                choices=[('equal', 'Equal'), ('not_equals', 'Not equal'),
                         ('greater_than', 'Greater than'),
                         ('less_than', 'Less than'), ('contains', 'Contains'),
                         ('not_contains', 'Not contains')], max_length=50),
        ),
        migrations.AlterField(
            model_name='fieldsetrule',
            name='type',
            field=models.CharField(choices=[('sum_equal', 'Sum equal'),
                                            ('validator', 'Validator')],
                                   max_length=50),
        ),
        migrations.AlterField(
            model_name='fieldsettemplaterule',
            name='type',
            field=models.CharField(choices=[('sum_equal', 'Sum equal'),
                                            ('validator', 'Validator')],
                                   max_length=50),
        ),
        migrations.AlterField(
            model_name='fieldtemplaterulegroupand',
            name='operator',
            field=models.CharField(
                choices=[('equal', 'Equal'), ('not_equals', 'Not equal'),
                         ('greater_than', 'Greater than'),
                         ('less_than', 'Less than'), ('contains', 'Contains'),
                         ('not_contains', 'Not contains')], max_length=50),
        ),
    ]
