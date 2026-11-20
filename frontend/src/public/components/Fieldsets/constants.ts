import { EFieldLabelPosition, ERuleCombinator } from '../../types/fieldset';

export const FIELDSET_RULES_MSG_RULE_REQUIRED = 'fieldsets.rules-validation-rule-required';
export const FIELDSET_RULES_MSG_VALUE_REQUIRED = 'fieldsets.rules-validation-value-required';
export const FIELDSET_RULES_MSG_VALUE_NUMBER = 'fieldsets.rules-validation-value-number';
export const FIELDSET_RULES_MSG_FIELDS_REQUIRED = 'fieldsets.rules-validation-fields-required';
export const FIELDSET_RULES_MSG_FIELDS_NUMBER = 'fieldsets.rules-validation-fields-number';

export const FIELDSET_RULE_COMBINATORS = [ERuleCombinator.And, ERuleCombinator.Or];

export const FIELDSET_LABEL_POSITION_OPTIONS: { value: EFieldLabelPosition; labelKey: string }[] = [
  { value: EFieldLabelPosition.Top, labelKey: 'fieldsets.settings.label-position.top' },
  { value: EFieldLabelPosition.Left, labelKey: 'fieldsets.settings.label-position.left' },
];
