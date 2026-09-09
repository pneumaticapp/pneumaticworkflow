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
import { EPermissionObjectType } from '../../../types/permissions';

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
  authUser: { isAccountOwner, timezone, dateFmt, language },
  permissions,
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
  // Editing the workflow is the same right the controls need, so it comes from the same answer
  // and stays false until the permissions request for this workflow lands.
  const canEdit = workflow ? Boolean(permissions[EPermissionObjectType.Workflow][workflow.id]?.hasChange) : false;

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
