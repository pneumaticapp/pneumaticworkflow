import * as React from 'react';
import { useMemo } from 'react';
import { useIntl } from 'react-intl';

import { IKickoff, IExtraField, ITemplateTask, EExtraFieldType } from '../../../../types/template';
import { TTaskVariable } from '../../types';
import { IGetLocalizedSystemVariableParams, IGetLocalizedSystemVariableReturn } from './types';
import { StepName } from '../../../StepName';
import { getPreviousTasks } from './getPreviousTasks';
import { EStartingType } from '../Conditions/utils/getDropdownOperators';

export const WORKFLOW_STARTER_VARIABLE_API_NAME = 'workflow-starter';
export const WORKFLOW_STARTER_VARIABLE_TITLE = 'Workflow starter';
export const SYSTEM_VARIABLE_SUBTITLE = 'System variable';

const SYSTEM_VARIABLE_API_NAMES = [WORKFLOW_STARTER_VARIABLE_API_NAME];
export const isSystemVariable = (apiName: string) => SYSTEM_VARIABLE_API_NAMES.includes(apiName);

export function getLocalizedSystemVariable({
  apiName,
  title,
  subtitle,
  formatMessage,
}: IGetLocalizedSystemVariableParams): IGetLocalizedSystemVariableReturn {
  if (!isSystemVariable(apiName)) {
    return {
      title,
      ...(subtitle !== undefined && { subtitle }),
    };
  }

  return {
    title: formatMessage({ id: `kickoff.system-varibale-${apiName}` }),
    ...(subtitle !== undefined && { subtitle: formatMessage({ id: 'kickoff.system-varibale' }) }),
  };
}

type TGetVariablesParam = {
  kickoff?: Pick<IKickoff, 'fields'>;
  tasks?: (Pick<ITemplateTask, 'fields'> & { name?: ITemplateTask['name'] })[];
  templateId?: number;
};

/**
 * This function duplicates the system variables defined in useWorkflowNameVariables hook
 * with hardcoded (non-localized) titles. It exists because getVariables() is called from
 * a Redux saga (templates/saga.ts), where React hooks cannot be used.
 * Localization of these titles is handled at render time via isSystemVariable() checks.
 * TODO: refactor to store only apiName/type in Redux, and localize in components.
 */
export function getSystemVariables(): TTaskVariable[] {
  return [
    {
      apiName: WORKFLOW_STARTER_VARIABLE_API_NAME,
      title: WORKFLOW_STARTER_VARIABLE_TITLE,
      subtitle: SYSTEM_VARIABLE_SUBTITLE,
      type: EExtraFieldType.String,
    },
  ];
}

export function getFieldVariables({ kickoff, tasks, templateId }: TGetVariablesParam): TTaskVariable[] {
  const tasksVariables = tasks
    ?.reduce((acc, task) => {
      const fieldsWithTasks = task.fields.map((field) => [task, field] as const);

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

  return [...(kickoffVariables || []), ...(tasksVariables || [])];
}

export function getVariables(params: TGetVariablesParam): TTaskVariable[] {
  return [...getSystemVariables(), ...getFieldVariables(params)];
}

export function getKickoffVariables(kickoff?: Pick<IKickoff, 'fields'>) {
  return kickoff?.fields.map((field) => getVariableFromField(field, 'Kick-off form')) || [];
}

export function getTaskVariables(
  kickoff: IKickoff,
  tasks: ITemplateTask[],
  currentTask: ITemplateTask,
  templateId?: number,
): TTaskVariable[] {
  return getFieldVariables({
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
    datasetId: field.dataset,
  };
}

const SINGLE_LINE_VARIBALE_TIPES = [
  EExtraFieldType.Number,
  EExtraFieldType.String,
  EExtraFieldType.User,
  EExtraFieldType.Date,
  EExtraFieldType.Radio,
  EExtraFieldType.Creatable,
  EExtraFieldType.Checkbox,
  EStartingType.Task,
  EStartingType.Kickoff,
];

export const getSingleLineVariables = (variables: TTaskVariable[]) => {
  return variables.filter((variable) => SINGLE_LINE_VARIBALE_TIPES.includes(variable.type));
};

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
      {
        apiName: 'workflow-id',
        title: formatMessage({ id: 'kickoff.system-varibale-workflow-id' }),
        subtitle: formatMessage({ id: 'kickoff.system-varibale' }),
        richSubtitle: null,
        type: EExtraFieldType.Number,
      },
      {
        apiName: 'workflow-starter',
        title: formatMessage({ id: 'kickoff.system-varibale-workflow-starter' }),
        subtitle: formatMessage({ id: 'kickoff.system-varibale' }),
        richSubtitle: null,
        type: EExtraFieldType.String,
      },
    ],
    [formatMessage],
  );

  const kickoffSingleLineVriables = getSingleLineVariables(getKickoffVariables(kickoff));

  return [...CUSTOM_VARIABLES, ...kickoffSingleLineVriables];
};
