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

import type { RootState } from '../../../redux/store';
import { EPermissionObjectType } from '../../../types/permissions';

import type { IWorkflowModalProps } from './WorkflowModal';
import { WorkflowModal } from './WorkflowModal';

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
}: RootState): TStoreProps {
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
