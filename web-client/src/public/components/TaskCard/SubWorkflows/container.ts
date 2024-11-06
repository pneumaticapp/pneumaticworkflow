import { connect } from 'react-redux';

import { SubWorkflows, TSubWorkflowsProps } from './SubWorkflows';
import { loadCurrentTask, openWorkflowLogPopup } from '../../../redux/actions';

type TDispatchProps = Pick<
TSubWorkflowsProps,
  | 'openWorkflowLogPopup'
  | 'loadCurrentTask'
>;

export const mapDispatchToProps: TDispatchProps = {
  openWorkflowLogPopup,
  loadCurrentTask
};

export const SubWorkflowsContainer = connect(null, mapDispatchToProps)(SubWorkflows);
