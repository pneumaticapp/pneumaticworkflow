import type { ReactNode } from 'react';
import type { TTaskVariable } from '../../../../../types/template';
import type { EConditionOperators, ICondition, TConditionRule } from '../../../../../types/templateTaskConditions';

export interface IDropdownOperator {
  operator: EConditionOperators;
  label: string;
}

export interface IGetOptionState {
  label: string | ReactNode;
  isSelected?: boolean;
}

export interface IGetFormattedDropdownOptionParams extends IGetOptionState {
  isTooltip?: boolean;
}

export interface IHandleAddNewConditionProps {
  order?: number;
  conditions: ICondition[];
  accessConditions: boolean;
  onEdit: (conditions: ICondition[]) => void;
  startTask?: boolean;
}

export interface IHandleAddNewRuleProps {
  conditionApiName: string;
  conditions: ICondition[];
  accessConditions: boolean;
  onEdit: (conditions: ICondition[]) => void;
}

export interface IGetDeletedFieldsProps {
  variables: TTaskVariable[];
  prevVariables?: TTaskVariable[];
  conditions: ICondition[];
  onEdit: (conditions: ICondition[]) => void;
}

export interface IGetDropdownStepsProps {
  startingOrder: TTaskVariable[];
  variables: TTaskVariable[];
  rule: TConditionRule;
}
