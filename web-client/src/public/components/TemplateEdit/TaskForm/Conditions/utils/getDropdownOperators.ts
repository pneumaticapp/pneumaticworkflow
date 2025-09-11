import { EConditionOperators } from '../types';
import { EExtraFieldType } from '../../../../../types/template';

export enum EStartingType {
  Task = 'task',
  Kickoff = 'kickoff',
}

export interface IDropdownOperator {
  operator: EConditionOperators;
  label: string;
}

export const conditionsByFieldTypeMap: { [key in EExtraFieldType]: EConditionOperators[] } & {
  [key in EStartingType]: EConditionOperators[];
} = {
  [EExtraFieldType.Number]: [
    EConditionOperators.Equal,
    EConditionOperators.NotEqual,
    EConditionOperators.Exist,
    EConditionOperators.NotExist,
    EConditionOperators.MoreThan,
    EConditionOperators.LessThan,
  ],
  [EExtraFieldType.String]: [
    EConditionOperators.Equal,
    EConditionOperators.NotEqual,
    EConditionOperators.Exist,
    EConditionOperators.NotExist,
    EConditionOperators.Contain,
    EConditionOperators.NotContain,
  ],
  [EExtraFieldType.Text]: [
    EConditionOperators.Equal,
    EConditionOperators.NotEqual,
    EConditionOperators.Exist,
    EConditionOperators.NotExist,
    EConditionOperators.Contain,
    EConditionOperators.NotContain,
  ],
  [EExtraFieldType.Date]: [
    EConditionOperators.Equal,
    EConditionOperators.NotEqual,
    EConditionOperators.Exist,
    EConditionOperators.NotExist,
    EConditionOperators.MoreThan,
    EConditionOperators.LessThan,
  ],
  [EExtraFieldType.Url]: [
    EConditionOperators.Equal,
    EConditionOperators.NotEqual,
    EConditionOperators.Exist,
    EConditionOperators.NotExist,
    EConditionOperators.Contain,
    EConditionOperators.NotContain,
  ],
  [EExtraFieldType.Checkbox]: [
    EConditionOperators.Equal,
    EConditionOperators.NotEqual,
    EConditionOperators.Exist,
    EConditionOperators.NotExist,
    EConditionOperators.Contain,
    EConditionOperators.NotContain,
  ],
  [EExtraFieldType.Radio]: [
    EConditionOperators.Equal,
    EConditionOperators.NotEqual,
    EConditionOperators.Exist,
    EConditionOperators.NotExist,
  ],
  [EExtraFieldType.Creatable]: [
    EConditionOperators.Equal,
    EConditionOperators.NotEqual,
    EConditionOperators.Exist,
    EConditionOperators.NotExist,
  ],
  [EExtraFieldType.File]: [EConditionOperators.Exist, EConditionOperators.NotExist],
  [EExtraFieldType.User]: [
    EConditionOperators.Equal,
    EConditionOperators.NotEqual,
    EConditionOperators.Exist,
    EConditionOperators.NotExist,
  ],
  [EStartingType.Task]: [EConditionOperators.Completed],
  [EStartingType.Kickoff]: [EConditionOperators.Completed],
};

export const labelByOperatorMap: { [key in EConditionOperators]: string } = {
  [EConditionOperators.Contain]: 'templates.conditions.contain',
  [EConditionOperators.NotContain]: 'templates.conditions.not-contain',
  [EConditionOperators.Equal]: 'templates.conditions.equal',
  [EConditionOperators.NotEqual]: 'templates.conditions.not-equal',
  [EConditionOperators.Exist]: 'templates.conditions.exist',
  [EConditionOperators.NotExist]: 'templates.conditions.not-exist',
  [EConditionOperators.LessThan]: 'templates.conditions.less-than',
  [EConditionOperators.MoreThan]: 'templates.conditions.more-than',
  [EConditionOperators.Completed]: 'templates.conditions.completed',
};

export function getDropdownOperators(
  fieldType: EExtraFieldType | EStartingType,
  messages: Record<string, string>,
): IDropdownOperator[] {
  return conditionsByFieldTypeMap[fieldType].map((operator) => {
    const labelIntlId = labelByOperatorMap[operator];

    return {
      operator,
      label: messages[labelIntlId],
    };
  });
}
