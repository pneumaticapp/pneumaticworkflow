import { connect } from 'react-redux';
import { markChecklistItem, unmarkChecklistItem } from '../../../../redux/actions';
import { getCurrentTask } from '../../../../redux/selectors/task';
import type { RootState } from '../../../../redux/store';
import { getTaskChecklistItem } from '../../../../utils/tasks';
import type { TTaskCheckableItemReduxProps, TTaskCheckableItemOwnProps } from './TaskCheckableItem';
import { TaskCheckableItem } from './TaskCheckableItem';

type TStoreProps = Pick<TTaskCheckableItemReduxProps, 'isChecked'>;
type TDispatchProps = Pick<TTaskCheckableItemReduxProps, 'markChecklistItem' | 'unmarkChecklistItem'>;

const mapStateToProps = (state: RootState, { listApiName, itemApiName }: TTaskCheckableItemOwnProps): TStoreProps => {
  const task = getCurrentTask(state);
  if (!task) {
    return {
      isChecked: false,
    };
  }

  const checklistItem = getTaskChecklistItem(task, listApiName, itemApiName);

  return {
    isChecked: checklistItem?.isSelected || false,
  };
};

const mapDispatchToProps: TDispatchProps = {
  markChecklistItem,
  unmarkChecklistItem,
};

export const TaskCheckableItemContainer = connect(mapStateToProps, mapDispatchToProps)(TaskCheckableItem);
