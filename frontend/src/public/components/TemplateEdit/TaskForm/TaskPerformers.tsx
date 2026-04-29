import React, { useCallback } from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';
import classNames from 'classnames';

import { Checkbox } from '../../UI/Fields/Checkbox';
import { InputField } from '../../UI/Fields/InputField';
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
  const isHierarchical = !!task.hierarchyConfig;

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

  // react-select filterOption expects FilterOptionOption<unknown>, not our domain type
  const handleFilterUsers = useCallback((option: { label: string }, text: string) => {
    const searchText = text.toLowerCase();

    return option.label.toLowerCase().includes(searchText);
  }, []);

  const handleAddInvitedPerformers = useCallback((invitedUsers: TUserListItem[]) => {
    const invitedPerformers: ITemplateTaskPerformer[] = invitedUsers
      .filter(({ id }) => {
        return !rawPerformers.some(({ type, sourceId }) => type === ETaskPerformerType.User && sourceId === String(id));
      })
      .map((user) => ({
        type: ETaskPerformerType.User,
        sourceId: String(user.id),
        label: getUserFullName(user),
        apiName: createPerformerApiName(),
      }));

    setCurrentTask({ rawPerformers: [...rawPerformers, ...invitedPerformers] });
  }, [rawPerformers, setCurrentTask]);

  const handleAddPerformer = useCallback((performer: ITemplateTaskPerformer) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { sourceId, type, label } = performer;
    const normalizedPerformer: ITemplateTaskPerformer = {
      sourceId,
      type,
      label,
      apiName: createPerformerApiName(),
    };

    setCurrentTask({ rawPerformers: [...rawPerformers, normalizedPerformer] as ITemplateTaskPerformer[] });
  }, [rawPerformers, setCurrentTask]);

  const handleRemovePerformer = useCallback((removingPerformer: ITemplateTaskPerformer) => {
    const newPerformers = rawPerformers.filter((performer) => {
      return ![
        performer.type === removingPerformer.type,
        !performer.sourceId || performer.sourceId === removingPerformer.sourceId,
      ].every(Boolean);
    });

    setCurrentTask({ rawPerformers: newPerformers });
  }, [rawPerformers, setCurrentTask]);

  const handleRequireCompletionByAllChange = useCallback((value: boolean) => {
    setCurrentTask({ requireCompletionByAll: value });
  }, [setCurrentTask]);

  const handleHierarchyToggle = useCallback((checked: boolean) => {
    if (checked) {
      setCurrentTask({
        hierarchyConfig: { maxDepth: null },
        requireCompletionByAll: false,
      });
    } else {
      setCurrentTask({ hierarchyConfig: null });
    }
  }, [setCurrentTask]);

  const handleMaxDepthChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setCurrentTask({
      hierarchyConfig: { maxDepth: val === '' ? null : parseInt(val, 10) }
    });
  }, [setCurrentTask]);

  const renderPerformers = () => {
    return (
      <ul className={styles['task-performers']}>
        {selectedPerformerOption.map((performer) => {
          return (
            <li className={styles['task-performers__item']} key={performer.apiName}>
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
      {!isHierarchical && (
        <div className={stylesTaskForm['content-mb']}>
          <Checkbox
            id="completeByAll"
            title={formatMessage({ id: 'templates.task-require-completion-by-all' })}
            checked={task.requireCompletionByAll}
            onChange={(e) => handleRequireCompletionByAllChange(e.currentTarget.checked)}
          />
        </div>
      )}
      <div className={stylesTaskForm['content-mb']}>
        <Checkbox
          id="hierarchicalApproval"
          title={formatMessage({ id: 'templates.hierarchical-approval-toggle' })}
          checked={isHierarchical}
          onChange={(e) => handleHierarchyToggle(e.currentTarget.checked)}
        />
      </div>
      {isHierarchical && (
        <div className={stylesTaskForm['content-mb']}>
          <InputField
            type="number"
            min="1"
            title={formatMessage({ id: 'templates.hierarchical-approval-depth' })}
            fieldSize="md"
            value={task.hierarchyConfig?.maxDepth || ''}
            onChange={handleMaxDepthChange}
          />
        </div>
      )}
      <div className={stylesTaskForm['content-mb']}>
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
