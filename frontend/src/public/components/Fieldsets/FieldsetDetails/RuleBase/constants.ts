import { EExtraFieldType } from '../../../../types/template';
import {
  EFieldsetRulesetNumericOperator,
  EFieldRuleOperator,
} from '../../../../types/fieldset';
import { TOperatorOption } from './types';

const operatorLabelMap: Record<EFieldRuleOperator, string> = {
  [EFieldRuleOperator.Equal]: 'templates.conditions.equal',
  [EFieldRuleOperator.NotEqual]: 'templates.conditions.not-equal',
  [EFieldRuleOperator.Contain]: 'templates.conditions.contain',
  [EFieldRuleOperator.NotContain]: 'templates.conditions.not-contain',
  [EFieldRuleOperator.GreaterThan]: 'templates.conditions.more-than',
  [EFieldRuleOperator.LessThan]: 'templates.conditions.less-than',
  [EFieldRuleOperator.Exist]: 'templates.conditions.exist',
  [EFieldRuleOperator.NotExist]: 'templates.conditions.not-exist',
};

const toOptions = (operators: EFieldRuleOperator[]): TOperatorOption[] =>
  operators.map((operator) => ({ value: operator, labelKey: operatorLabelMap[operator] }));

const textLikeOperators = toOptions([
  EFieldRuleOperator.Equal,
  EFieldRuleOperator.NotEqual,
  EFieldRuleOperator.Exist,
  EFieldRuleOperator.NotExist,
  EFieldRuleOperator.Contain,
  EFieldRuleOperator.NotContain,
]);

const numericOperators = toOptions([
  EFieldRuleOperator.Equal,
  EFieldRuleOperator.NotEqual,
  EFieldRuleOperator.Exist,
  EFieldRuleOperator.NotExist,
  EFieldRuleOperator.GreaterThan,
  EFieldRuleOperator.LessThan,
]);

const selectionOperators = toOptions([
  EFieldRuleOperator.Equal,
  EFieldRuleOperator.NotEqual,
  EFieldRuleOperator.Exist,
  EFieldRuleOperator.NotExist,
]);

const fileOperators = toOptions([
  EFieldRuleOperator.Exist,
  EFieldRuleOperator.NotExist,
]);

export const fieldRuleOperatorsByFieldTypeMap: Record<EExtraFieldType, TOperatorOption[]> = {
  [EExtraFieldType.Number]: numericOperators,
  [EExtraFieldType.Date]: numericOperators,
  [EExtraFieldType.String]: textLikeOperators,
  [EExtraFieldType.Text]: textLikeOperators,
  [EExtraFieldType.Url]: textLikeOperators,
  [EExtraFieldType.Checkbox]: textLikeOperators,
  [EExtraFieldType.Radio]: selectionOperators,
  [EExtraFieldType.Creatable]: selectionOperators,
  [EExtraFieldType.User]: selectionOperators,
  [EExtraFieldType.File]: fileOperators,
};

export const FIELDSET_RULESET_NUMERIC_OPERATOR_OPTIONS: TOperatorOption[] = [
  { value: EFieldsetRulesetNumericOperator.SumEqual, labelKey: 'fieldsets.rule-type-sum_equal' },
  { value: EFieldsetRulesetNumericOperator.SumGreaterThan, labelKey: 'fieldsets.rule-type-sum_greater_than' },
  { value: EFieldsetRulesetNumericOperator.SumLessThan, labelKey: 'fieldsets.rule-type-sum_less_than' },
];
