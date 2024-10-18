import { connect } from 'react-redux';
import { IWorkflowControllsProps, WorkflowControllsComponents } from './WorkflowControlls';
import { IApplicationState } from '../../../types/redux';

type TStoreProps = Pick<IWorkflowControllsProps, 'timezone'>;

function mapStateToProps({
  authUser: { timezone },
}: IApplicationState): TStoreProps {
  return {
    timezone
  };
}

export const WorkflowControlls = connect(mapStateToProps)(WorkflowControllsComponents);
