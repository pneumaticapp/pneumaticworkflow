import type { IGetLocalizedSystemVariableParams, IGetLocalizedSystemVariableReturn } from './types';

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
