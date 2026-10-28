import { IntlShape } from 'react-intl';

import { ITemplateClient } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';
import { validateWorkflowName } from '../../../utils/validators';
import { PremiumFeaturesWarning, IInfoWarningProps } from '../InfoWarningsModal/warnings';

type TWarningRule<T> = {
  check(): boolean;
  getMessage(): T;
};

export function validateTemplate(template: ITemplateClient, isSubscribed: boolean, intl: IntlShape) {
  const { owners, name, tasks } = template;
  const { formatMessage } = intl;

  const commonWarningRules: TWarningRule<string>[] = [
    {
      check: () => !owners.length,
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
  ];

  const infoWarningRules: TWarningRule<(props: IInfoWarningProps) => JSX.Element>[] = [
    {
      check: () => {
        if (isSubscribed) {
          return false;
        }
        const hasTaskWithConditionRules = tasks.some(({ conditions }) =>
          conditions.some(({ rules }) => isArrayWithItems(rules)),
        );

        return hasTaskWithConditionRules;
      },
      getMessage: () => PremiumFeaturesWarning,
    },
  ];

  const getWarnings = <T>(rules: TWarningRule<T>[]) =>
    rules.filter(({ check }) => check()).map(({ getMessage }) => getMessage());

  return {
    commonWarnings: getWarnings(commonWarningRules),
    infoWarnings: getWarnings(infoWarningRules),
  };
}
