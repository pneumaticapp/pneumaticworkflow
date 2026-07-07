import { ITemplate } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';
import { validateWorkflowName } from '../../../utils/validators';
import { ETaskFormParts } from '../types';
import { PremiumFeaturesWarning, UnassignedTasksWarning } from '../InfoWarningsModal/warnings';
import { collectExtraFieldErrors } from './collectExtraFieldErrors';
import { collectConditionErrors } from './collectConditionErrors';
import { TTemplateValidationError, TTemplateValidationResult } from './types';

export function collectTemplateValidationErrors(
  template: ITemplate,
  isSubscribed: boolean,
): TTemplateValidationResult {
  const { owners, name, tasks, kickoff } = template;
  const blockingErrors: TTemplateValidationError[] = [];

  if (!owners.length) {
    blockingErrors.push({
      path: 'owners',
      messageId: 'template.no-run-allowers',
      scrollTarget: { area: 'owners' },
    });
  }

  if (!tasks.length) {
    blockingErrors.push({
      path: 'tasks',
      messageId: 'template.no-tasks',
      scrollTarget: { area: 'tasks' },
    });
  }

  const nameError = validateWorkflowName(name);
  if (nameError) {
    blockingErrors.push({
      path: 'name',
      messageId: nameError,
      scrollTarget: { area: 'name' },
    });
  }

  if (kickoff?.fields) {
    blockingErrors.push(
      ...collectExtraFieldErrors(kickoff.fields, 'kickoff', (fieldApiName) => ({
        area: 'kickoff',
        fieldApiName,
      })),
    );
  }

  tasks.forEach((task) => {
    blockingErrors.push(
      ...collectExtraFieldErrors(task.fields, `tasks.${task.uuid}`, (fieldApiName) => ({
        area: 'task',
        taskUuid: task.uuid,
        formPart: ETaskFormParts.Fields,
        fieldApiName,
      })),
    );

    blockingErrors.push(...collectConditionErrors(task.uuid, task.conditions));
  });

  const infoWarnings: TTemplateValidationResult['infoWarnings'] = [];

  if (tasks.some((task) => !isArrayWithItems(task.rawPerformers))) {
    infoWarnings.push(UnassignedTasksWarning);
  }

  if (!isSubscribed && tasks.some(({ conditions }) => conditions.some(({ rules }) => isArrayWithItems(rules)))) {
    infoWarnings.push(PremiumFeaturesWarning);
  }

  return { blockingErrors, infoWarnings };
}

export function getValidationErrorMap(errors: TTemplateValidationError[]): Record<string, string> {
  return errors.reduce<Record<string, string>>((map, error) => {
    map[error.path] = error.messageId;
    return map;
  }, {});
}
