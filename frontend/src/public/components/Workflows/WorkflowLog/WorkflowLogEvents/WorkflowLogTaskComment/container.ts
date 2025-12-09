import { connect } from 'react-redux';
import { editComment } from '../../../../../redux/workflows/actions';
import { deleteReactionComment, createReactionComment, watchedComment } from '../../../../../redux/workflows/slice';
import { TWorkflowLogTaskCommentProps, WorkflowLogTaskComment } from './WorkflowLogTaskComment';
import { deleteComment } from '../../../../../redux/actions';
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
