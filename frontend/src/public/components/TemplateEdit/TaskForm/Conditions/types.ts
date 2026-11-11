import type { TTaskVariable } from '../../../../types/template';
import type { ICondition } from '../../../../types/templateTaskConditions';
import type { TUserListItem } from '../../../../types/user';

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
