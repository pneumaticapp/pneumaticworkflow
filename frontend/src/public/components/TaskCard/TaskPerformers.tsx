import React, { ElementRef, useEffect, useRef } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { ETaskStatus } from '../../redux/actions';
import { getRegularGroupsList } from '../../redux/selectors/groups';
import { ETaskPerformerType, ETemplateOwnerType } from '../../types/template';
import { TUserListItem } from '../../types/user';
import { EWorkflowStatus } from '../../types/workflow';
import { trackInviteTeamInPage } from '../../utils/analytics';
import { getUserFullName } from '../../utils/users';
import UserDataWithGroup from '../UserDataWithGroup';
import { EBgColorTypes, UserPerformer } from '../UI/UserPerformer';
import { EOptionTypes, getUsersDropdownOptionValue, TUsersDropdownOption, UsersDropdown } from '../UI/form/UsersDropdown';
import { GuestController } from './GuestsController';
import { ETaskCardViewMode, TTaskPerformersProps } from './types';

import styles from './TaskCard.css';

export function TaskPerformers({
  task,
  viewMode,
  workflow,
  status,
  users,
  authUser,
  addTaskPerformer,
  removeTaskPerformer,
}: TTaskPerformersProps) {
  const { formatMessage } = useIntl();
  const groups = useSelector(getRegularGroupsList);
  const guestsControllerRef = useRef<ElementRef<typeof GuestController> | null>(null);
  const canRemovePerformer = [
    task.performers.length > 1,
    viewMode !== ETaskCardViewMode.Guest,
    status !== ETaskStatus.Completed,
    workflow?.status !== EWorkflowStatus.Finished,
    !task.isReadOnlyViewer,
  ].every(Boolean);

  useEffect(() => {
    guestsControllerRef.current?.updateDropdownPosition();
  }, [task.performers.length]);

  const onUsersInvited = (invitedUsers: TUserListItem[]) => {
    invitedUsers.forEach((user) =>
      addTaskPerformer({
        taskId: task.id,
        userId: { sourceId: user.id, type: ETemplateOwnerType.User },
      }),
    );
  };
  const onRemoveTaskPerformer = ({ id, optionType }: TUsersDropdownOption) => {
    removeTaskPerformer({
      taskId: task.id,
      userId: { sourceId: id, type: optionType as unknown as ETemplateOwnerType },
    });
  };
  const onAddTaskPerformer = ({ id, optionType }: TUsersDropdownOption) => {
    addTaskPerformer({
      taskId: task.id,
      userId: { sourceId: id, type: optionType as unknown as ETemplateOwnerType },
    });
  };
  const userOptions = users.map((user) => ({
    ...user,
    optionType: EOptionTypes.User,
    label: getUserFullName(user),
    value: getUsersDropdownOptionValue(EOptionTypes.User, user.id),
  }));
  const selectedUsers = users
    .filter((user) => task.performers.some(
      ({ sourceId, type }) => Number(sourceId) === user.id && type === ETemplateOwnerType.User,
    ))
    .map((user) => ({
      ...user,
      optionType: EOptionTypes.User,
      label: getUserFullName(user),
      value: getUsersDropdownOptionValue(EOptionTypes.User, user.id),
    }));
  const groupOptions = groups.map((group) => ({
    ...group,
    optionType: EOptionTypes.Group,
    type: ETaskPerformerType.UserGroup,
    label: group.name,
    value: getUsersDropdownOptionValue(EOptionTypes.Group, group.id),
  }));
  const selectedGroups = groups
    .filter((group) => task.performers.some(
      ({ sourceId, type }) => Number(sourceId) === group.id && type === ETemplateOwnerType.UserGroup,
    ))
    .map((group) => ({
      ...group,
      optionType: EOptionTypes.Group,
      label: group.name,
      value: getUsersDropdownOptionValue(EOptionTypes.Group, group.id),
    }));
  const canEditPerformers = status !== ETaskStatus.Completed
    && workflow?.status !== EWorkflowStatus.Finished
    && !task.isReadOnlyViewer;

  return (
    <>
      {canEditPerformers && authUser.isAdmin && (
        <UsersDropdown
          isMulti
          controlSize="sm"
          className={classnames(styles.responsible, 'no-print')}
          placeholder={formatMessage({ id: 'user.search-field-placeholder' })}
          options={[...groupOptions, ...userOptions]}
          value={[...selectedUsers, ...selectedGroups]}
          onChange={onAddTaskPerformer}
          onChangeSelected={onRemoveTaskPerformer}
          onUsersInvited={onUsersInvited}
          onClickInvite={() => trackInviteTeamInPage('Task card')}
          inviteLabel={formatMessage({ id: 'template.invite-team-member' })}
          title={formatMessage({ id: 'task.add-performer' })}
        />
      )}
      {canEditPerformers && viewMode !== ETaskCardViewMode.Guest && (
        <GuestController
          ref={guestsControllerRef}
          taskId={task.id}
          className={classnames(styles['guest-dropdown'], 'no-print')}
        />
      )}
      {task.performers.map((performer) => {
        const onClick = canRemovePerformer
          ? () => removeTaskPerformer({ taskId: task.id, userId: performer })
          : undefined;

        if (performer.type === ETemplateOwnerType.UserGroup && performer.label) {
          return (
            <UserPerformer
              key={performer.sourceId}
              user={{ ...performer, sourceId: String(performer.sourceId), value: String(performer.sourceId) }}
              bgColor={EBgColorTypes.Light}
              onClick={onClick}
            />
          );
        }

        return (
          <UserDataWithGroup key={performer.sourceId} idItem={performer.sourceId} type={performer.type}>
            {(user) => (
              <UserPerformer
                user={{
                  ...user,
                  sourceId: String(user.id),
                  value: String(user.id),
                  label: getUserFullName(user),
                }}
                bgColor={EBgColorTypes.Light}
                onClick={onClick}
              />
            )}
          </UserDataWithGroup>
        );
      })}
    </>
  );
}
