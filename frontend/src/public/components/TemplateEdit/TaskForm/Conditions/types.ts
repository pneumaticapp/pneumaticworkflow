import { EExtraFieldType } from '../../../../types/template';
import { EStartingType } from './utils/getDropdownOperators';

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
  field: string | null;
  operator: EConditionOperators | null;
} & TConditionPredicateValue;

export interface ITypedConditionPredicateValue<FieldType, ValueType> {
  fieldType?: FieldType;
  value?: ValueType | null;
}

export type TConditionPredicateValue =
  | ITypedConditionPredicateValue<EExtraFieldType.String, string>
  | ITypedConditionPredicateValue<EExtraFieldType.Text, string>
  | ITypedConditionPredicateValue<EExtraFieldType.Creatable, number>
  | ITypedConditionPredicateValue<EExtraFieldType.Checkbox, number>
  | ITypedConditionPredicateValue<EExtraFieldType.Radio, number>
  | ITypedConditionPredicateValue<EExtraFieldType.Date, string>
  | ITypedConditionPredicateValue<EExtraFieldType.File, null>
  | ITypedConditionPredicateValue<EExtraFieldType.Url, string>
  | ITypedConditionPredicateValue<EExtraFieldType.User, number>
  | ITypedConditionPredicateValue<EStartingType.Task, null>
  | ITypedConditionPredicateValue<EStartingType.Kickoff, null>
  | ITypedConditionPredicateValue<EExtraFieldType.Number, number>;

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
  Completed = 'completed',
}

export enum EConditionLogicOperations {
  And = 'and',
  Or = 'or',
}
