import { connect } from 'react-redux';
import { markChecklistItem, unmarkChecklistItem } from '../../../../redux/actions';
import { getCurrentTask } from '../../../../redux/selectors/task';
import { IApplicationState } from '../../../../types/redux';
import { getTaskChecklistItem } from '../../../../utils/tasks';
import { TaskCheckableItem, TTaskCheckableItemReduxProps, TTaskCheckableItemOwnProps } from './TaskCheckableItem';

type TStoreProps = Pick<TTaskCheckableItemReduxProps, 'isChecked'>;
type TDispatchProps = Pick<TTaskCheckableItemReduxProps, 'markChecklistItem' | 'unmarkChecklistItem'>;

const mapStateToProps = (
  state: IApplicationState,
  { listApiName, itemApiName }: TTaskCheckableItemOwnProps): TStoreProps => {
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
}

export const TaskCheckableItemContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(TaskCheckableItem);
