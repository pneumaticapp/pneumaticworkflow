import { connect } from 'react-redux';

import type { TSubWorkflowsProps } from './SubWorkflows';
import { SubWorkflows } from './SubWorkflows';
import { loadCurrentTask } from '../../../redux/actions';
import { openWorkflowLogPopup } from '../../../redux/workflows/slice';

type TDispatchProps = Pick<TSubWorkflowsProps, 'openWorkflowLogPopup' | 'loadCurrentTask'>;

export const mapDispatchToProps: TDispatchProps = {
  openWorkflowLogPopup,
  loadCurrentTask,
};

export const SubWorkflowsContainer = connect(null, mapDispatchToProps)(SubWorkflows);
