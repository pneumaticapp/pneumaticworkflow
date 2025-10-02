import { connect } from 'react-redux';
import { closeRunWorkflowModal, runWorkflow } from '../../redux/actions';
import { IApplicationState } from '../../types/redux';
import { INullableWorkflowEditPopupProps, WorkflowEditPopup } from './WorkflowEditPopup';

type TStoreProps = Pick<INullableWorkflowEditPopupProps, 'isLoading' | 'isOpen' | 'workflow' | 'accountId' | 'isAdmin' | 'timezone'>;
type TDispatchProps = Pick<INullableWorkflowEditPopupProps, 'onRunWorkflow' | 'closeModal'>;

function mapStateToProps({
  runWorkflowModal: {
    isOpen,
    isWorkflowStarting,
    workflow,
  },
  authUser: { account, isAdmin, timezone },
}: IApplicationState): TStoreProps {
  return {
    isLoading: isWorkflowStarting,
    isOpen,
    timezone,
    workflow,
    accountId: account.id || -1,
    isAdmin: Boolean(isAdmin),
  };
}

const mapDispatchToProps: TDispatchProps = {
  closeModal: closeRunWorkflowModal,
  onRunWorkflow: runWorkflow,
};

export const WorkflowEditPopupContainer = connect(mapStateToProps, mapDispatchToProps)(WorkflowEditPopup);
