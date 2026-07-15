import { EFieldLabelPosition, EFieldsetRuleType } from '../../types/fieldset';

export const FIELDSET_RULES_MSG_INCOMPLETE = 'fieldsets.rules-validation-incomplete';
export const FIELDSET_RULES_MSG_VALUE_REQUIRED = 'fieldsets.rules-validation-value-required';
export const FIELDSET_RULES_MSG_VALUE_NUMBER = 'fieldsets.rules-validation-value-number';
export const FIELDSET_RULES_MSG_FIELDS_REQUIRED = 'fieldsets.rules-validation-fields-required';
export const FIELDSET_RULES_MSG_FIELDS_NUMBER = 'fieldsets.rules-validation-fields-number';

export const NUMBER_RULE_TYPES = new Set<EFieldsetRuleType>([EFieldsetRuleType.SumEqual]);

export const FIELDSET_RULE_TYPES = [
  { value: EFieldsetRuleType.SumEqual, labelKey: 'fieldsets.rule-type-sum_equal' },
];

export const FIELDSET_RULE_VALUE_PLACEHOLDER_BY_TYPE: Record<EFieldsetRuleType, string> = {
  [EFieldsetRuleType.SumEqual]: 'fieldsets.rule-value-placeholder-number',
};

export const FIELDSET_LABEL_POSITION_OPTIONS: { value: EFieldLabelPosition; labelKey: string }[] = [
  { value: EFieldLabelPosition.Top, labelKey: 'fieldsets.settings.label-position.top' },
  { value: EFieldLabelPosition.Left, labelKey: 'fieldsets.settings.label-position.left' },
];
