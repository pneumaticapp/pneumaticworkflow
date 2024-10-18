/* eslint-disable */
/* prettier-ignore */
import { EExtraFieldType } from '../../../../types/template';

export interface IChecklists {
  id?: number;
  apiName: string;
  order: number;
  rules: TConditionRule[];
  action: EConditionAction;
}

export interface ICondition {
  id?: number;
  apiName: string;
  order: number;
  rules: TConditionRule[];
  action: EConditionAction;
}

export type TConditionRule = {
  ruleId?: number;
  ruleApiName: string;
  predicateId?: number;
  predicateApiName: string;
  logicOperation: EConditionLogicOperations;
  field: string;
  operator: EConditionOperators | null;
} & TConditionPredicateValue;

export interface ITypedConditionPredicateValue<FieldType, ValueType> {
  fieldType?: FieldType;
  value?: ValueType;
}

export type TConditionPredicateValue =
  ITypedConditionPredicateValue<EExtraFieldType.String, string>
  | ITypedConditionPredicateValue<EExtraFieldType.Text, string>
  | ITypedConditionPredicateValue<EExtraFieldType.Creatable, number>
  | ITypedConditionPredicateValue<EExtraFieldType.Checkbox, number>
  | ITypedConditionPredicateValue<EExtraFieldType.Radio, number>
  | ITypedConditionPredicateValue<EExtraFieldType.Date, string>
  | ITypedConditionPredicateValue<EExtraFieldType.File, null>
  | ITypedConditionPredicateValue<EExtraFieldType.Url, string>
  | ITypedConditionPredicateValue<EExtraFieldType.User, number>;

export enum EConditionAction {
  SkipTask = 'skip_task',
  StartTask = 'start_task',
  EndProcess = 'end_process',
}

export enum EConditionOperators {
  Equal = 'equals',
  NotEqual = 'not_equals',
  Exist = 'exists',
  NotExist = 'not_exists',
  Contain = 'contains',
  NotContain = 'not_contains',
  MoreThan = 'more_than',
  LessThan = 'less_than',
}

export enum EConditionLogicOperations {
  And = 'and',
  Or = 'or',
}
