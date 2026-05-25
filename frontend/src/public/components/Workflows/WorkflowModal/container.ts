import { connect } from 'react-redux';

import {
  closeWorkflowLogPopup,
  changeWorkflowLogViewSettings,
  setIsEditWorkflowName,
  setIsEditKickoff,
  setWorkflowEdit,
  sendWorkflowLogComments,
  editWorkflow,
  toggleSkippedTasksVisibility,
} from '../../../redux/workflows/slice';

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
  | 'isSkippedTasksShown'
  | 'isLogLoading'
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
  | 'toggleSkippedTasksVisibility'
  | 'sendWorkflowLogComments'
  | 'setIsEditWorkflowName'
  | 'setIsEditKickoff'
  | 'editWorkflow'
  | 'setWorkflowEdit'
  | 'toggleModal'
>;

export function mapStateToProps({
  authUser: { id: currentUserId, isAccountOwner, isAdmin, timezone, dateFmt, language },
  workflows: {
    workflowLog: {
      workflowId,
      isCommentsShown,
      isOnlyAttachmentsShown,
      isSkippedTasksShown,
      isOpen,
      items,
      sorting,
      isLoading: isLogLoading,
    },
    isWorkflowLoading,
    workflow,
    workflowEdit,
  },
  runWorkflowModal: { isOpen: isRunWorkflowOpen },
  general: {
    fullscreenImage: { isOpen: isFullscreenImageOpen },
  },
}: IApplicationState): TStoreProps {
  const isWorkflowOwner = workflow?.owners?.some((id) => id === currentUserId) ?? false;
  const canEdit = Boolean(isAccountOwner) || (isWorkflowOwner && Boolean(isAdmin));

  return {
    dateFmt,
    timezone,
    workflowId,
    isAccountOwner,
    workflow,
    canEdit,
    workflowEdit,
    isCommentsShown,
    isLogLoading,
    isOnlyAttachmentsShown,
    isSkippedTasksShown,
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
  toggleSkippedTasksVisibility,
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
