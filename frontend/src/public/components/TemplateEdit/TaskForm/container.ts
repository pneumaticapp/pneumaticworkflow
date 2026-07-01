import { connect } from 'react-redux';

import { TaskForm, ITaskFormProps } from './TaskForm';
import { IApplicationState } from '../../../types/redux';
import { getIsUserSubsribed } from '../../../redux/selectors/user';

type TStoreProps = Pick<ITaskFormProps, 'isSubscribed' | 'accountId' | 'isTeamInvitesModalOpen'>;
type TOwnProps = Pick<ITaskFormProps, 'task'>;

const mapStateToProps = (state: IApplicationState): TStoreProps => {
  const {
    authUser: { account },
    team: { isInvitesPopupOpen: isTeamInvitesModalOpen },
  } = state;
  const isSubscribed = getIsUserSubsribed(state);

  return {
    isSubscribed,
    accountId: account.id || -1,
    isTeamInvitesModalOpen,
  };
};

export const WorkflowTaskFormContainer = connect<TStoreProps, {}, TOwnProps>(mapStateToProps)(TaskForm);
