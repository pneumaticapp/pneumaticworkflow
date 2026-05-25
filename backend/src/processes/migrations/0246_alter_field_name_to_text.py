# Generated manually: remove 120-char limit on kickoff/task field labels (FieldMixin.name)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0245_add_templateowner_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fieldtemplate',
            name='name',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='taskfield',
            name='name',
            field=models.TextField(),
        ),
    ]
