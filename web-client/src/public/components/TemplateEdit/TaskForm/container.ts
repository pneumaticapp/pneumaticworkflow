/* eslint-disable */
/* prettier-ignore */
import { connect } from 'react-redux';

import { TaskForm, ITaskFormProps } from './TaskForm';
import { IApplicationState } from '../../../types/redux';
import { getTaskVariables, getVariables } from './utils/getTaskVariables';
import { patchTask } from '../../../redux/actions';
import { getIsUserSubsribed } from '../../../redux/selectors/user';

type TStoreProps = Pick<
  ITaskFormProps,
  'listVariables' | 'templateVariables' | 'isSubscribed' | 'accountId' | 'isTeamInvitesModalOpen' | 'kickoff' | 'tasks'
>;
type TDispatchProps = Pick<ITaskFormProps, 'patchTask'>;
type TOwnProps = Pick<ITaskFormProps, 'task'>;

const mapStateToProps = (state: IApplicationState, { task }: TOwnProps): TStoreProps => {
  const {
    template: {
      data: { kickoff, tasks, id },
    },
    authUser: { account },
    teamInvites: { isInvitesPopupOpen: isTeamInvitesModalOpen },
  } = state;
  const isSubscribed = getIsUserSubsribed(state);

  return {
    listVariables: getTaskVariables(kickoff, tasks, task, id),
    templateVariables: getVariables({ kickoff, tasks, templateId: id }),
    isSubscribed,
    accountId: account.id || -1,
    isTeamInvitesModalOpen,
    kickoff,
    tasks,
  };
};

const mapDispatchToProps: TDispatchProps = { patchTask };

export const WorkflowTaskFormContainer = connect(mapStateToProps, mapDispatchToProps)(TaskForm);
