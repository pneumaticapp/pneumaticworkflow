import type { TMarkChecklistItemPayload, TUnmarkChecklistItemPayload } from '../../../../redux/task/actions';

export type TTaskCheckableItemOwnProps = {
  listApiName: string;
  itemApiName: string;
  disabled?: boolean;
};

export type TTaskCheckableItemReduxProps = {
  isChecked: boolean;
  markChecklistItem(payload: TMarkChecklistItemPayload): void;
  unmarkChecklistItem(payload: TUnmarkChecklistItemPayload): void;
};

export type TTaskCheckableItemProps = TTaskCheckableItemOwnProps & TTaskCheckableItemReduxProps;
