/* eslint-disable */
/* prettier-ignore */
import { IntlShape } from 'react-intl';

import { ITemplate } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';
import { validateWorkflowName } from '../../../utils/validators';
import { UnassignedTasksWarning, PremiumFeaturesWarning, IInfoWarningProps } from '../InfoWarningsModal/warnings';
import { areConditionsValid } from '../TaskForm/Conditions/utils/conditionsValidators';
import { areExtraFieldsValid } from './areExtraFieldsValid';
import { isValidTaskForm } from './isValidTaskForm';

type TWarningRule<T> = {
  check(): boolean;
  getMessage(): T;
};

export function validateTemplate(template: ITemplate, isSubscribed: boolean, intl: IntlShape) {
  const { templateOwners, name, tasks, kickoff } = template;
  const { formatMessage } = intl;

  const taskWithInvalidConditions = tasks.filter(task => !areConditionsValid(task.conditions));

  const commonWarningRules: TWarningRule<string>[] = [
    {
      check: () => !templateOwners.length,
      getMessage: () => formatMessage({ id: 'template.no-run-allowers' }),
    },
    {
      check: () => !tasks.length,
      getMessage: () => formatMessage({ id: 'template.no-tasks' }),
    },
    {
      check: () => Boolean(validateWorkflowName(name)),
      getMessage: () => formatMessage({ id: validateWorkflowName(name) }),
    },
    {
      check: () => !tasks.every(isValidTaskForm),
      getMessage: () => formatMessage({ id: 'template.task-validation-error' }),
    },
    {
      check: () => !areExtraFieldsValid(kickoff!.fields),
      getMessage: () => formatMessage({ id: 'template.kickoff-validation-error' }),
    },
    {
      check: () => isArrayWithItems(taskWithInvalidConditions),
      getMessage: () => {
        const baseMessage = formatMessage({ id: 'template.task-conditions-validation-error' });
        const formattedTaskNames = taskWithInvalidConditions.map(({ name }) => name).join(',\n');
        const message = `${baseMessage}\n${formattedTaskNames}`;

        return message;
      },
    },
  ];

  const infoWarningRules: TWarningRule<((props: IInfoWarningProps) => JSX.Element)>[] = [
    {
      check: () => {
        const hasTaskWithoutPerformers = tasks.some(task => !isArrayWithItems(task.rawPerformers));

        return hasTaskWithoutPerformers;
      },
      getMessage: () => UnassignedTasksWarning,
    },
    {
      check: () => {
        if (isSubscribed) {
          return false;
        }
        const hasTaskWithConditionRules = tasks
          .some(({ conditions }) => conditions.some(({ rules }) => isArrayWithItems(rules)));

        return hasTaskWithConditionRules;
      },
      getMessage: () => PremiumFeaturesWarning,
    },
  ];

  const getWarnings = <T>(rules: TWarningRule<T>[]) => rules
    .filter(({ check }) => check())
    .map(({ getMessage }) => getMessage());

  return {
    commonWarnings: getWarnings(commonWarningRules),
    infoWarnings: getWarnings(infoWarningRules),
  };
}
