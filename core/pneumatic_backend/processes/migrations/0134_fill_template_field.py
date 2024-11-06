# 2021-06-06 14:38
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('processes', '0133_auto_20210603_1305'),
    ]

    operations = [
        migrations.RunSQL(sql="""
          UPDATE processes_fieldtemplate ft SET template_id = t.template_id
          FROM processes_tasktemplate t WHERE ft.task_id = t.id;
          
          UPDATE processes_fieldtemplate ft SET template_id = k.template_id
          FROM processes_kickoff k WHERE ft.kickoff_id = k.id;
          
          UPDATE processes_fieldtemplateselection fts
            SET template_id = ft.template_id
          FROM processes_fieldtemplate ft 
          WHERE fts.field_template_id = ft.id;
          
          UPDATE processes_conditiontemplate ct SET template_id = t.template_id
          FROM processes_tasktemplate t WHERE ct.task_id = t.id;
          
          UPDATE processes_ruletemplate rt SET template_id = ct.template_id
          FROM processes_conditiontemplate ct WHERE rt.condition_id = ct.id;
          
          UPDATE processes_predicatetemplate pt 
            SET template_id = rt.template_id
          FROM processes_ruletemplate rt WHERE pt.rule_id = rt.id;
          
          DELETE FROM processes_fieldtemplateselection
            WHERE template_id IS NULL;
          DELETE FROM processes_tasktemplate_output_responsible
            WHERE fieldtemplate_id IN (
              SELECT id FROM processes_fieldtemplate WHERE template_id IS NULL
            ) OR 
            tasktemplate_id IN (
              SELECT id FROM processes_tasktemplate WHERE template_id IS NULL
            );
          DELETE FROM processes_fieldtemplate WHERE template_id IS NULL;
          DELETE FROM processes_ruletemplate WHERE template_id IS NULL;
          DELETE FROM processes_predicatetemplate WHERE template_id IS NULL;
          DELETE FROM processes_conditiontemplate WHERE template_id IS NULL;
          DELETE FROM processes_tasktemplate_responsible 
            WHERE tasktemplate_id IN (
            SELECT id FROM processes_tasktemplate WHERE template_id IS NULL
          );
          DELETE FROM processes_tasktemplate WHERE template_id IS NULL;
        """)
    ]
