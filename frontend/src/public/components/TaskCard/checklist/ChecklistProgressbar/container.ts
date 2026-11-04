import { connect } from 'react-redux';
import { getCurrentTask } from '../../../../redux/selectors/task';
import type { RootState } from '../../../../redux/store';
import { getTaskChecklist } from '../../../../utils/tasks';
import {
  TChecklistProgressbarReduxProps,
  TChecklistProgressbarOwnProps,
  ChecklistProgressbar,
} from './ChecklistProgressbar';

type TStoreProps = Pick<TChecklistProgressbarReduxProps, 'totalItems' | 'checkedItems'>;

const mapStateToProps = (state: RootState, { listApiName }: TChecklistProgressbarOwnProps): TStoreProps => {
  const task = getCurrentTask(state);
  if (!task) {
    return {
      totalItems: 1,
      checkedItems: 0,
    };
  }

  const checklist = getTaskChecklist(task, listApiName);

  return {
    totalItems: checklist?.totalItems || 1,
    checkedItems: checklist?.checkedItems || 0,
  };
};

export const ChecklistProgressbarContainer = connect(mapStateToProps)(ChecklistProgressbar);
