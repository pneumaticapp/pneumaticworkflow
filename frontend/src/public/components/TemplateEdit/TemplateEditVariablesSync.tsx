import { useEffect } from 'react';

import { ITemplateClient } from '../../types/template';
import { TLoadTemplateVariablesSuccessPayload } from '../../redux/actions';
import { getVariables } from './TaskForm/utils/getTaskVariables';

export interface ITemplateEditVariablesSyncProps {
  template: ITemplateClient;
  prevTemplate: ITemplateClient | undefined;
  loadTemplateVariablesSuccess(payload: TLoadTemplateVariablesSuccessPayload): void;
}

export function TemplateEditVariablesSync({
  template,
  prevTemplate,
  loadTemplateVariablesSuccess,
}: ITemplateEditVariablesSyncProps) {
  useEffect(() => {
    const variables = getVariables({
      kickoff: template.kickoff,
      tasks: template.tasks,
      templateId: template.id,
    });
    let prevVariables = [];
    if (prevTemplate) {
      prevVariables = getVariables({
        kickoff: prevTemplate.kickoff,
        tasks: prevTemplate.tasks,
        templateId: prevTemplate.id,
      });
    }

    if (variables.length !== prevVariables.length && template.id) {
      loadTemplateVariablesSuccess({ templateId: template.id, variables });
    }
  }, [loadTemplateVariablesSuccess, prevTemplate, template]);

  return null;
}
