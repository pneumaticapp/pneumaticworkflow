import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';

import { IKickoff, IExtraField, ITemplateTask, EExtraFieldType } from '../../../../types/template';
import { TTaskVariable } from '../../types';
import { StepName } from '../../../StepName';
import { getPreviousTasks } from './getPreviousTasks';

type TGetVariablesParam = {
  kickoff?: Pick<IKickoff, 'fields'>;
  tasks?: (Pick<ITemplateTask, 'fields'> & { name?: ITemplateTask['name'] })[];
  templateId?: number;
};

export function getVariables({ kickoff, tasks, templateId }: TGetVariablesParam) {
  const tasksVariables = tasks
    ?.reduce((acc, task) => {
      const fieldsWithTasks = task.fields.map(field => [task, field] as const);

      return [...acc, ...fieldsWithTasks];
    }, [])
    .map(([task, field]) => {
      const taskName = task.name || '';

      return getVariableFromField(
        field,
        taskName,
        templateId ? <StepName initialStepName={taskName} templateId={templateId} /> : taskName,
      );
    });

  const kickoffVariables = getKickoffVariables(kickoff);

  return [
    ...(kickoffVariables || []),
    ...(tasksVariables || []),
  ];
}

export function getKickoffVariables(kickoff?: Pick<IKickoff, 'fields'>) {
  return kickoff?.fields.map(field => getVariableFromField(field, 'Kick-off form')) || [];
}

export function getTaskVariables(
  kickoff: IKickoff,
  tasks: ITemplateTask[],
  currentTask: ITemplateTask,
  templateId?: number,
): TTaskVariable[] {
  return getVariables({
    kickoff,
    tasks: getPreviousTasks(currentTask, tasks),
    templateId,
  });
}

export function getVariableFromField(
  field: IExtraField,
  subtitle: string,
  richSubtitle?: React.ReactNode,
): TTaskVariable {
  return {
    apiName: field.apiName,
    title: field.name,
    subtitle,
    richSubtitle: richSubtitle || subtitle,
    type: field.type,
    selections: field.selections,
  };
}

const SINGLE_LINE_VARIBALE_TIPES = [
  EExtraFieldType.String,
  EExtraFieldType.User,
  EExtraFieldType.Date,
  EExtraFieldType.Radio,
  EExtraFieldType.Creatable,
  EExtraFieldType.Checkbox,
];

export const getSingleLineVariables = (variables: TTaskVariable[]) => {
  return variables.filter(variable => SINGLE_LINE_VARIBALE_TIPES.includes(variable.type));
}

export const useWorkflowNameVariables = (kickoff?: Pick<IKickoff, 'fields'>) => {
  const { formatMessage } = useIntl();

  const CUSTOM_VARIABLES: TTaskVariable[] = useMemo(
    () => [
      {
        apiName: 'date',
        title: formatMessage({ id: 'kickoff.system-varibale-date' }),
        subtitle: formatMessage({ id: 'kickoff.system-varibale' }),
        richSubtitle: null,
        type: EExtraFieldType.Date,
      },
      {
        apiName: 'template-name',
        title: formatMessage({ id: 'kickoff.system-varibale-template-name' }),
        subtitle: formatMessage({ id: 'kickoff.system-varibale' }),
        richSubtitle: null,
        type: EExtraFieldType.String,
      },
    ],
    [formatMessage],
  );

  const kickoffSingleLineVriables = getSingleLineVariables(getKickoffVariables(kickoff));

  return [...CUSTOM_VARIABLES, ...kickoffSingleLineVriables];
}