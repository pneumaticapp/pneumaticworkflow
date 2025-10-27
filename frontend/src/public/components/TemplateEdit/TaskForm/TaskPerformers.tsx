import React from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';
import classNames from 'classnames';

import { Checkbox } from '../../UI/Fields/Checkbox';
import { TUserListItem } from '../../../types/user';
import { ETaskPerformerType, ITemplateTask, ITemplateTaskPerformer } from '../../../types/template';
import { TTaskVariable } from '../types';
import { trackInviteTeamInPage } from '../../../utils/analytics';
import { TUsersDropdownOption, UsersDropdown } from '../../UI/form/UsersDropdown';
import { getUserFullName } from '../../../utils/users';
import { getPerformersForDropdown } from './utils/getPerformersForDropdown';
import { EBgColorTypes, UserPerformer } from '../../UI/UserPerformer';
import { IApplicationState } from '../../../types/redux';

import styles from '../TemplateEdit.css';
import stylesTaskForm from './TaskForm.css';
import { createPerformerApiName } from '../../../utils/createId';

export interface ITaskPerformersProps {
  task: ITemplateTask;
  users: TUserListItem[];
  variables: TTaskVariable[];
  isTeamInvitesModalOpen: boolean;
  setCurrentTask(changedFields: Partial<ITemplateTask>): void;
}

export function TaskPerformers({ task, users, variables, setCurrentTask }: ITaskPerformersProps) {
  const { formatMessage } = useIntl();
  const groups = useSelector((state: IApplicationState) => state.groups.list);

  const { rawPerformers = [] } = task;

  const dropdownPerformersOption: TUsersDropdownOption[] = getPerformersForDropdown(
    users,
    groups,
    variables,
    formatMessage,
  );
  const selectedPerformerOption = rawPerformers.map((user) => {
    return {
      ...user,
      value: String(user.sourceId),
    };
  });

  const handleFilterUsers = (option: any, text: string) => {
    const searchText = text.toLowerCase();

    if (option.label.toLowerCase().includes(searchText)) {
      return true;
    }

    return false;
  };

  const handleAddInvitedPerformers = (invitedUsers: TUserListItem[]) => {
    const invitedPeformers: ITemplateTaskPerformer[] = invitedUsers
      .filter(({ id }) => {
        return !rawPerformers.some(({ type, sourceId }) => type === ETaskPerformerType.User && sourceId === String(id));
      })
      .map((user) => ({
        type: ETaskPerformerType.User,
        sourceId: String(user.id),
        label: getUserFullName(user),
        apiName: createPerformerApiName(),
      }));

    setCurrentTask({ rawPerformers: [...rawPerformers, ...invitedPeformers] });
  };

  const handleAddPerformer = (performer: ITemplateTaskPerformer) => {
    const normalizedPerformer = { ...performer, apiName: createPerformerApiName() };
    delete (normalizedPerformer as any).id;
    setCurrentTask({ rawPerformers: [...rawPerformers, normalizedPerformer] as ITemplateTaskPerformer[] });
  };

  const handleRemovePerformer = (removingPerformer: ITemplateTaskPerformer) => {
    const newPerformers = rawPerformers.filter((performer) => {
      return ![
        performer.type === removingPerformer.type,
        !performer.sourceId || performer.sourceId === removingPerformer.sourceId,
      ].every(Boolean);
    });

    setCurrentTask({ rawPerformers: newPerformers });
  };

  const handleRequireCompletionByAllChange = (value: boolean) => {
    setCurrentTask({ requireCompletionByAll: value });
  };

  const renderPerformers = () => {
    return (
      <ul className={styles['task-performers']}>
        {selectedPerformerOption.map((performer) => {
          return (
            <li className={styles['task-performers__item']}>
              <UserPerformer
                user={performer}
                bgColor={EBgColorTypes.Light}
                onClick={() => handleRemovePerformer(performer)}
              />
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <div className={classNames(styles['task-fields-wrapper'], stylesTaskForm['content-mt16'])}>
      <div className="mb-3">
        <Checkbox
          id="completeByAll"
          title={formatMessage({ id: 'templates.task-require-completion-by-all' })}
          checked={task.requireCompletionByAll}
          onChange={(e) => handleRequireCompletionByAllChange(e.currentTarget.checked)}
        />
      </div>
      <div className="mb-3">
        <UsersDropdown
          isMulti
          className={styles['responsible']}
          placeholder={formatMessage({ id: 'user.search-field-placeholder' })}
          options={dropdownPerformersOption}
          value={selectedPerformerOption}
          onChange={handleAddPerformer}
          onChangeSelected={handleRemovePerformer}
          filterOption={handleFilterUsers}
          onClickInvite={() => trackInviteTeamInPage('Assign performers')}
          onUsersInvited={handleAddInvitedPerformers}
          inviteLabel={formatMessage({ id: 'template.invite-team-member' })}
        />
      </div>
      {renderPerformers()}
    </div>
  );
}
