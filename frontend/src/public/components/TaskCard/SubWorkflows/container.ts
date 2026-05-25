import { connect } from 'react-redux';

import { SubWorkflows, TSubWorkflowsProps } from './SubWorkflows';
import { loadCurrentTask } from '../../../redux/actions';
import { openWorkflowLogPopup } from '../../../redux/workflows/slice';

type TDispatchProps = Pick<TSubWorkflowsProps, 'openWorkflowLogPopup' | 'loadCurrentTask'>;

export const mapDispatchToProps: TDispatchProps = {
  openWorkflowLogPopup,
  loadCurrentTask,
};

export const SubWorkflowsContainer = connect(null, mapDispatchToProps)(SubWorkflows);
