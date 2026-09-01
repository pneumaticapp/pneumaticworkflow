import { EExtraFieldType } from '../../../../types/template';
import { EFieldRuleShowOperator } from './types';

const textLikeOperators: EFieldRuleShowOperator[] = [
  EFieldRuleShowOperator.Equal,
  EFieldRuleShowOperator.NotEqual,
  EFieldRuleShowOperator.Exist,
  EFieldRuleShowOperator.NotExist,
  EFieldRuleShowOperator.Contain,
  EFieldRuleShowOperator.NotContain,
];

const numericOperators: EFieldRuleShowOperator[] = [
  EFieldRuleShowOperator.Equal,
  EFieldRuleShowOperator.NotEqual,
  EFieldRuleShowOperator.Exist,
  EFieldRuleShowOperator.NotExist,
  EFieldRuleShowOperator.GreaterThan,
  EFieldRuleShowOperator.LessThan,
];

const selectionOperators: EFieldRuleShowOperator[] = [
  EFieldRuleShowOperator.Equal,
  EFieldRuleShowOperator.NotEqual,
  EFieldRuleShowOperator.Exist,
  EFieldRuleShowOperator.NotExist,
];

const fileOperators: EFieldRuleShowOperator[] = [
  EFieldRuleShowOperator.Exist,
  EFieldRuleShowOperator.NotExist,
];

export const fieldRuleShowOperatorsByFieldTypeMap: Record<EExtraFieldType, EFieldRuleShowOperator[]> = {
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

export const fieldRuleShowOperatorLabelMap: Record<EFieldRuleShowOperator, string> = {
  [EFieldRuleShowOperator.Equal]: 'templates.conditions.equal',
  [EFieldRuleShowOperator.NotEqual]: 'templates.conditions.not-equal',
  [EFieldRuleShowOperator.Contain]: 'templates.conditions.contain',
  [EFieldRuleShowOperator.NotContain]: 'templates.conditions.not-contain',
  [EFieldRuleShowOperator.GreaterThan]: 'templates.conditions.more-than',
  [EFieldRuleShowOperator.LessThan]: 'templates.conditions.less-than',
  [EFieldRuleShowOperator.Exist]: 'templates.conditions.exist',
  [EFieldRuleShowOperator.NotExist]: 'templates.conditions.not-exist',
};
