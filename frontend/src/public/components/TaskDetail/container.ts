import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import { ITaskDetailProps, TaskDetail } from './TaskDetail';
import { loadCurrentTask } from '../../redux/actions';
import { IApplicationState } from '../../types/redux';

type TTaskDetailDispatchProps = Pick<ITaskDetailProps, 'loadCurrentTask'>;
type TTaskDetailStoreProps = Pick<ITaskDetailProps, 'task'>;

export function mapStateToProps( { task: { data: task } }: IApplicationState): TTaskDetailStoreProps {
  return { task };
}

export const mapDispatchToProps: TTaskDetailDispatchProps = { loadCurrentTask };

export const TaskDetailContainer = withRouter(connect(mapStateToProps, mapDispatchToProps)(TaskDetail));
