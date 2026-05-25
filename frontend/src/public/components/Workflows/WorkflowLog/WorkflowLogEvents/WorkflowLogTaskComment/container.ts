import { connect } from 'react-redux';
import {
  deleteReactionComment,
  createReactionComment,
  watchedComment,
  editComment,
  deleteComment } from '../../../../../redux/workflows/slice';
import { TWorkflowLogTaskCommentProps, WorkflowLogTaskComment } from './WorkflowLogTaskComment';

import { IApplicationState } from '../../../../../types/redux';

type TStoreProps = Pick<TWorkflowLogTaskCommentProps, 'currentUserId' | 'workflowModal'>;
type TDispatchProps = Pick<
  TWorkflowLogTaskCommentProps,
  'deleteComment' | 'editComment' | 'watchedComment' | 'createReactionComment' | 'deleteReactionComment'
>;

export function mapStateToProps({
  authUser: { id: currentUserId },
  workflows: {
    workflowLog: { isOpen },
  },
}: IApplicationState): TStoreProps {
  return {
    currentUserId,
    workflowModal: isOpen,
  };
}

export const mapDispatchToProps: TDispatchProps = {
  editComment,
  deleteComment,
  watchedComment,
  createReactionComment,
  deleteReactionComment,
};

export const WorkflowLogTaskCommentContainer = connect(mapStateToProps, mapDispatchToProps)(WorkflowLogTaskComment);
