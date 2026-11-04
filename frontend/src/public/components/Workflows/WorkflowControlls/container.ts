import { connect } from 'react-redux';
import { IWorkflowControllsProps, WorkflowControllsComponents } from './WorkflowControlls';
import type { RootState } from '../../../redux/store';

type TStoreProps = Pick<IWorkflowControllsProps, 'timezone'>;

function mapStateToProps({ authUser: { timezone } }: RootState): TStoreProps {
  return {
    timezone,
  };
}

export const WorkflowControlls = connect(mapStateToProps)(WorkflowControllsComponents);
