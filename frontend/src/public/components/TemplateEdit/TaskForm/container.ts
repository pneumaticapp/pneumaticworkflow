import { connect } from 'react-redux';

import type { ITaskFormProps } from './TaskForm';
import { TaskForm } from './TaskForm';
import type { RootState } from '../../../redux/store';
import { patchTask } from '../../../redux/actions';
import { getIsUserSubsribed } from '../../../redux/selectors/user';

type TStoreProps = Pick<
  ITaskFormProps,
  'isSubscribed' | 'accountId' | 'isTeamInvitesModalOpen' | 'kickoff' | 'tasks'
> & { templateId: number | undefined };
type TDispatchProps = Pick<ITaskFormProps, 'patchTask'>;

const mapStateToProps = (state: RootState): TStoreProps => {
  const {
    template: {
      data: { kickoff, tasks, id },
    },
    authUser: { account },
    team: { isInvitesPopupOpen: isTeamInvitesModalOpen },
  } = state;
  const isSubscribed = getIsUserSubsribed(state);

  return {
    isSubscribed,
    accountId: account.id || -1,
    isTeamInvitesModalOpen,
    kickoff,
    tasks,
    templateId: id,
  };
};

const mapDispatchToProps: TDispatchProps = { patchTask };

export const WorkflowTaskFormContainer = connect(mapStateToProps, mapDispatchToProps)(TaskForm);
