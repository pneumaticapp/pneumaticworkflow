from django.db import migrations, models
import django.db.models.deletion
import src.generics.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0144_auto_20260609_1910'),
        ('processes', '0254_add_fileattachment_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='FieldSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('api_name', models.CharField(max_length=200)),
                ('label_position', models.CharField(choices=[('top', 'Top'), ('left', 'Left')], default='top', max_length=20)),
                ('name', models.TextField(max_length=1000)),
                ('title', models.TextField(blank=True, default='')),
                ('order', models.IntegerField(default=0)),
                ('description', models.TextField(blank=True, default='')),
                ('layout', models.CharField(choices=[('horizontal', 'Horizontal'), ('vertical', 'Vertical')], default='vertical', max_length=200)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
                ('kickoff', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fieldsets', to='processes.KickoffValue')),
            ],
            options={
                'ordering': ['-id'],
            },
            bases=(src.generics.mixins.models.SoftDeleteMixin, models.Model),
        ),
        migrations.CreateModel(
            name='FieldSetRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('api_name', models.CharField(max_length=200)),
                ('type', models.CharField(choices=[('sum_equal', 'The sum is equal')], max_length=50)),
                ('value', models.TextField(blank=True, null=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
                ('fieldset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='processes.FieldSet')),
            ],
            options={
                'ordering': ['-id'],
            },
            bases=(src.generics.mixins.models.SoftDeleteMixin, models.Model),
        ),
        migrations.CreateModel(
            name='FieldsetTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('api_name', models.CharField(max_length=200)),
                ('label_position', models.CharField(choices=[('top', 'Top'), ('left', 'Left')], default='top', max_length=20)),
                ('name', models.TextField(max_length=1000)),
                ('title', models.TextField(blank=True, default='')),
                ('order', models.IntegerField(default=0)),
                ('description', models.TextField(blank=True, default='')),
                ('layout', models.CharField(choices=[('horizontal', 'Horizontal'), ('vertical', 'Vertical')], default='vertical', max_length=200)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('is_shared', models.BooleanField(default=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
                ('kickoff', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fieldsets', to='processes.Kickoff')),
                ('shared_fieldset', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_fieldsets', to='processes.FieldsetTemplate')),
                ('task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fieldsets', to='processes.TaskTemplate')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fieldsets', to='processes.Template')),
            ],
            options={
                'ordering': ['-id'],
            },
            bases=(src.generics.mixins.models.SoftDeleteMixin, models.Model),
        ),
        migrations.CreateModel(
            name='FieldsetTemplateRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('api_name', models.CharField(max_length=200)),
                ('type', models.CharField(choices=[('sum_equal', 'The sum is equal')], max_length=50)),
                ('value', models.TextField(blank=True, null=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
                ('fieldset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='processes.FieldsetTemplate')),
            ],
            options={
                'ordering': ['-id'],
            },
            bases=(src.generics.mixins.models.SoftDeleteMixin, models.Model),
        ),
        migrations.AlterField(
            model_name='fieldtemplate',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='processes.Template'),
        ),
        migrations.AlterField(
            model_name='fieldtemplateselection',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='selections', to='processes.Template'),
        ),
        migrations.AddField(
            model_name='fieldset',
            name='task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fieldsets', to='processes.Task'),
        ),
        migrations.AddField(
            model_name='fieldset',
            name='workflow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fieldsets', to='processes.Workflow'),
        ),
        migrations.AddField(
            model_name='fieldtemplate',
            name='fieldset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='processes.FieldsetTemplate'),
        ),
        migrations.AddField(
            model_name='fieldtemplate',
            name='rules',
            field=models.ManyToManyField(blank=True, related_name='fields', to='processes.FieldsetTemplateRule'),
        ),
        migrations.AddField(
            model_name='taskfield',
            name='fieldset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='processes.FieldSet'),
        ),
        migrations.AddField(
            model_name='taskfield',
            name='rules',
            field=models.ManyToManyField(blank=True, related_name='fields', to='processes.FieldSetRule'),
        ),
        migrations.AddConstraint(
            model_name='fieldsettemplaterule',
            constraint=models.UniqueConstraint(condition=models.Q(is_deleted=False), fields=('api_name', 'fieldset'), name='fieldsettemplate_rule_api_name_template_unique'),
        ),
        migrations.AddConstraint(
            model_name='fieldsettemplate',
            constraint=models.UniqueConstraint(condition=models.Q(is_deleted=False), fields=('api_name', 'template', 'is_shared'), name='fieldsettemplate_template_api_name_is_shared_unique'),
        ),
    ]
