import { useEffect } from 'react';

import { ITemplate } from '../../types/template';
import { TLoadTemplateVariablesSuccessPayload } from '../../redux/actions';
import { getVariables } from './TaskForm/utils/getTaskVariables';

import { useTemplateEditFieldsets } from './TemplateEditFieldsetsContext';

export interface ITemplateEditVariablesSyncProps {
  template: ITemplate;
  prevTemplate: ITemplate | undefined;
  loadTemplateVariablesSuccess(payload: TLoadTemplateVariablesSuccessPayload): void;
}

export function TemplateEditVariablesSync({
  template,
  prevTemplate,
  loadTemplateVariablesSuccess,
}: ITemplateEditVariablesSyncProps) {
  const { fieldsetsById } = useTemplateEditFieldsets();

  useEffect(() => {
    const variables = getVariables({
      kickoff: template.kickoff,
      tasks: template.tasks,
      templateId: template.id,
      fieldsetsById,
    });
    let prevVariables = [];
    if (prevTemplate) {
      prevVariables = getVariables({
        kickoff: prevTemplate.kickoff,
        tasks: prevTemplate.tasks,
        templateId: prevTemplate.id,
        fieldsetsById,
      });
    }

    if (variables.length !== prevVariables.length && template.id) {
      loadTemplateVariablesSuccess({ templateId: template.id, variables });
    }
  }, [fieldsetsById, loadTemplateVariablesSuccess, prevTemplate, template]);

  return null;
}
