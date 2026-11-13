import type { TTaskVariable } from '../../../../types/template';
import type { EConditionOperators, ICondition, TConditionRule } from '../../../../types/templateTaskConditions';
import type { TUserListItem } from '../../../../types/user';
import type { IDropdownOperator } from './utils/types';

export interface IConditionsProps {
  conditions: ICondition[];
  startingOrder: TTaskVariable[];
  variables: TTaskVariable[];
  users: TUserListItem[];
  isSubscribed: boolean;
  onEdit(value: ICondition[]): void;
}

export interface IDropdownVariable extends TTaskVariable {
  label: string;
  richLabel: any;
}

export interface IPredicateProps {
  rule: TConditionRule;
  ruleIndex: number;
  accessConditions: boolean;
  changeCurrentRule: (changedFields: Partial<TConditionRule>) => void;
  displayedVariable: IDropdownVariable | null;
  isDisabledOperator: boolean;
  selectedOperator: IDropdownOperator | null;
  dropdownOperators: IDropdownOperator[];
  selectedVariable?: IDropdownVariable | null;
  users?: TUserListItem[];
  handleRemoveRule: (conditionIndex?: number) => (ruleIndex: number) => () => void;
  conditionIndex?: number;
  isCheckIs?: boolean;
  options: {
    label: string;
    options: IDropdownVariable[];
  }[];
}

export interface IRichLabelProps {
  variables: TTaskVariable[];
  variable: TTaskVariable;
  isSelected?: boolean;
  isFromStartingOrder?: boolean;
}

export interface IConditionValueFieldProps {
  variable: TTaskVariable | null;
  rule: TConditionRule;
  users: TUserListItem[];
  operator?: EConditionOperators | null;
  isDisabled: boolean;
  changeRuleValue(value: TConditionRule[keyof TConditionRule], kind?: 'user' | 'group'): void;
}

export interface IDropdownSelection {
  value: string;
  label: string;
}

export interface IDropdownUser extends TUserListItem {
  label: string;
  entityType: 'user' | 'group';
  value: string;
}
