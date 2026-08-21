import {
  EFieldLabelPosition,
  EFieldsetNumberRulesetOperator,
  ERuleCombinator,
} from '../../types/fieldset';

export const FIELDSET_RULES_MSG_INCOMPLETE = 'fieldsets.rules-validation-incomplete';
export const FIELDSET_RULES_MSG_VALUE_REQUIRED = 'fieldsets.rules-validation-value-required';
export const FIELDSET_RULES_MSG_VALUE_NUMBER = 'fieldsets.rules-validation-value-number';
export const FIELDSET_RULES_MSG_FIELDS_REQUIRED = 'fieldsets.rules-validation-fields-required';
export const FIELDSET_RULES_MSG_FIELDS_NUMBER = 'fieldsets.rules-validation-fields-number';

export const NUMBER_RULE_TYPES = new Set<EFieldsetNumberRulesetOperator>([
  EFieldsetNumberRulesetOperator.SumEqual,
  EFieldsetNumberRulesetOperator.SumGreaterThan,
  EFieldsetNumberRulesetOperator.SumLessThan,
]);

export const FIELDSET_RULE_OPERATOR_OPTIONS: {
  value: EFieldsetNumberRulesetOperator;
  labelKey: string;
}[] = [
  { value: EFieldsetNumberRulesetOperator.SumEqual, labelKey: 'fieldsets.rule-type-sum_equal' },
  { value: EFieldsetNumberRulesetOperator.SumGreaterThan, labelKey: 'fieldsets.rule-type-sum_greater_than' },
  { value: EFieldsetNumberRulesetOperator.SumLessThan, labelKey: 'fieldsets.rule-type-sum_less_than' },
];

export const FIELDSET_RULE_COMBINATORS = [ERuleCombinator.And, ERuleCombinator.Or];

export const FIELDSET_LABEL_POSITION_OPTIONS: { value: EFieldLabelPosition; labelKey: string }[] = [
  { value: EFieldLabelPosition.Top, labelKey: 'fieldsets.settings.label-position.top' },
  { value: EFieldLabelPosition.Left, labelKey: 'fieldsets.settings.label-position.left' },
];
