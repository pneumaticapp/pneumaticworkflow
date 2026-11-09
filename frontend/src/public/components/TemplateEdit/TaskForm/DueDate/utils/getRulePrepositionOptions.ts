import { TDueDateRulePreposition, TDueDateRuleTarget } from '../../../../../types/template';
import type { IntlShape } from 'react-intl';
import { TDropdownOptionBase } from '../../../../UI';

export type TRulePrepositionOption = TDropdownOptionBase & {
  rulePreposition: TDueDateRulePreposition;
};

export const getRulePrepositionOptions = (
  ruleTarget: TDueDateRuleTarget | null,
  formatMessage?: IntlShape['formatMessage'],
): TRulePrepositionOption[] => {
  const beforePreposition: TRulePrepositionOption = {
    label: formatMessage ? formatMessage({ id: 'due-date.before' }) : 'before',
    rulePreposition: 'before',
  };
  const afterPreposition: TRulePrepositionOption = {
    label: formatMessage ? formatMessage({ id: 'due-date.after' }) : 'after',
    rulePreposition: 'after',
  };

  if (!ruleTarget || ruleTarget === 'field') {
    return [beforePreposition, afterPreposition];
  }

  return [afterPreposition];
};
