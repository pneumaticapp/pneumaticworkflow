import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import { Avatar, FilterSelect } from '../../components/UI';
import { IApplicationState } from '../../types/redux';
import { setFilterWorkflowStarters as setWorkflowsFilterWorkflowStarters } from '../../redux/workflows/slice';
import { EXTERNAL_USER, getActiveUsers, getUserFullName } from '../../utils/users';
import { StarterFilterIcon } from '../../components/icons';
import styles from './WorkflowsLayout.css';
import { ERenderPlaceholderType, getRenderPlaceholder } from './utils';

export function StarterFilterSelect() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const { workflowStartersIdsFilter } = useSelector(
    (state: IApplicationState) => state.workflows.workflowsSettings.values,
  );
  const { workflowStartersCounters } = useSelector(
    (state: IApplicationState) => state.workflows.workflowsSettings.counters,
  );
  const { users } = useSelector((state: IApplicationState) => state.accounts);

  const activeUsers = getActiveUsers(users);

  const workflowStartersOptions = useMemo(() => {
    const usersWithExternal = [EXTERNAL_USER, ...activeUsers];

    const normalizedUsers = usersWithExternal.map((user) => {
      const userFullName = getUserFullName(user);
      const workflowsCount = workflowStartersCounters.find(({ sourceId }) => sourceId === user.id)?.workflowsCount || 0;
      return {
        ...user,
        displayName: (
          <div className={styles['user']}>
            <Avatar user={user} className={styles['user-avatar']} size="sm" />
            <span className={styles['user-name']}>{userFullName}</span>
          </div>
        ),
        ...(workflowsCount > 0 && { count: workflowsCount }),
        searchByText: userFullName,
      };
    });

    return normalizedUsers;
  }, [users.length, workflowStartersCounters]);

  return (
    <div className={styles['starter-filter']}>
      <FilterSelect
        isMultiple
        isSearchShown
        noValueLabel={formatMessage({ id: 'sorting.all-starters' })}
        placeholderText={formatMessage({ id: 'workflows.filter-no-starter' })}
        searchPlaceholder={formatMessage({ id: 'sorting.search-placeholder' })}
        selectedOptions={workflowStartersIdsFilter}
        options={workflowStartersOptions}
        optionIdKey="id"
        optionLabelKey="displayName"
        onChange={(workflowStarters: number[]) => dispatch(setWorkflowsFilterWorkflowStarters(workflowStarters))}
        resetFilter={() => dispatch(setWorkflowsFilterWorkflowStarters([]))}
        Icon={StarterFilterIcon}
        renderPlaceholder={() =>
          getRenderPlaceholder({
            filterIds: workflowStartersIdsFilter,
            options: workflowStartersOptions,
            formatMessage,
            type: ERenderPlaceholderType.Starter,
            severalOptionPlaceholder: 'sorting.several-starters',
            defaultPlaceholder: 'sorting.all-starters',
          })
        }
      />
    </div>
  );
}
