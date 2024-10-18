import { connect } from 'react-redux';

import {
  changeWorkflowLogViewSettings,
  setIsEditWorkflowName,
  setIsEditKickoff,
  editWorkflow,
  setWorkflowEdit,
  sendWorkflowLogComments,
  closeWorkflowLogPopup,
} from '../../../redux/workflows/actions';
import { IApplicationState } from '../../../types/redux';

import { WorkflowModal, IWorkflowModalProps } from './WorkflowModal';

export type TStoreProps = Pick<
  IWorkflowModalProps,
  | 'isAccountOwner'
  | 'isOpen'
  | 'timezone'
  | 'dateFmt'
  | 'sorting'
  | 'isCommentsShown'
  | 'isOnlyAttachmentsShown'
  | 'workflow'
  | 'items'
  | 'canEdit'
  | 'workflowEdit'
  | 'isLoading'
  | 'workflowId'
  | 'isRunWorkflowOpen'
  | 'isFullscreenImageOpen'
  | 'language'
>;

export type TDispatchProps = Pick<
  IWorkflowModalProps,
  | 'changeWorkflowLogViewSettings'
  | 'sendWorkflowLogComments'
  | 'setIsEditWorkflowName'
  | 'setIsEditKickoff'
  | 'editWorkflow'
  | 'setWorkflowEdit'
  | 'toggleModal'
>;

export function mapStateToProps({
  authUser: { id: currentUserId, isAccountOwner, timezone, dateFmt, language },
  workflows: {
    workflowLog: { workflowId, isCommentsShown, isOnlyAttachmentsShown, isOpen, items, sorting },
    isWorkflowLoading,
    workflow,
    workflowEdit,
  },
  runWorkflowModal: { isOpen: isRunWorkflowOpen },
  general: {
    fullscreenImage: { isOpen: isFullscreenImageOpen },
  },
}: IApplicationState): TStoreProps {
  const isTemplateOwner = workflow?.template?.templateOwners?.some((id) => id === currentUserId);

  const canEdit = [isAccountOwner, isTemplateOwner].some(Boolean);

  return {
    dateFmt,
    timezone,
    workflowId,
    isAccountOwner,
    workflow,
    canEdit,
    workflowEdit,
    isCommentsShown,
    isOnlyAttachmentsShown,
    isLoading: isWorkflowLoading,
    isOpen,
    items,
    sorting,
    isRunWorkflowOpen,
    isFullscreenImageOpen,
    language,
  };
}

export const mapDispatchToProps: TDispatchProps = {
  changeWorkflowLogViewSettings,
  sendWorkflowLogComments,
  setIsEditWorkflowName,
  setIsEditKickoff,
  editWorkflow,
  setWorkflowEdit,
  toggleModal: closeWorkflowLogPopup,
};

export const WorkflowModalContainer = connect<TStoreProps, TDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(WorkflowModal);
