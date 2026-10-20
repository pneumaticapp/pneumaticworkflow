import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import { Avatar } from '../../components/UI';
import { DropdownList } from '../../components/UI/DropdownList';
import {
  cancelCurrentPerformersCounters,
  cancelTemplateTasksCounters,
  setFilterWorkflowStarters as setWorkflowsFilterWorkflowStarters,
} from '../../redux/workflows/slice';
import { EXTERNAL_USER, getActiveUsers, getUserFullName } from '../../utils/users';
import { StarterFilterIcon } from '../../components/icons';
import styles from './WorkflowsLayout.css';
import { ERenderPlaceholderType, getRenderPlaceholder } from './utils';
import {
  getWorkflowsStatus,
  getWorkflowStartersCounters,
  getWorkflowStartersIdsFilter,
} from '../../redux/selectors/workflows';
import { getAccountsUsers } from '../../redux/selectors/accounts';
import { canFilterByTemplateStep } from '../../utils/workflows/filters';
import { useMobileMenuPortalProps } from './useMobileMenuPortalProps';

export function StarterFilterSelect() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const menuPortalProps = useMobileMenuPortalProps();

  const workflowStartersIdsFilter = useSelector(getWorkflowStartersIdsFilter);
  const workflowStartersCounters = useSelector(getWorkflowStartersCounters);
  const users = useSelector(getAccountsUsers);
  const statusFilter = useSelector(getWorkflowsStatus);

  const activeUsers = useMemo(() => getActiveUsers(users), [users]);

  const workflowStartersOptions = useMemo(() => {
    const usersWithExternal = [EXTERNAL_USER, ...activeUsers];

    const normalizedUsers = usersWithExternal.map((user) => {
      const userFullName = getUserFullName(user);
      const workflowsCount = workflowStartersCounters.find(({ sourceId }) => sourceId === user.id)?.workflowsCount || 0;
      return {
        ...user,
        value: String(user.id),
        label: (
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
  }, [activeUsers, workflowStartersCounters]);

  return (
    <DropdownList
      controlSize="sm"
      controlVariant="accent"
      Icon={StarterFilterIcon}
      isMulti
      isSearchable
      title={getRenderPlaceholder({
        filterIds: workflowStartersIdsFilter,
        options: workflowStartersOptions,
        formatMessage,
        type: ERenderPlaceholderType.Starter,
        severalOptionPlaceholder: 'sorting.several-starters',
        defaultPlaceholder: 'sorting.all-starters',
      })}
      placeholder={formatMessage({ id: 'sorting.search-placeholder' })}
      noOptionsMessage={() => formatMessage({ id: 'workflows.filter-no-starter' })}
      options={workflowStartersOptions}
      value={workflowStartersOptions.filter((option) => workflowStartersIdsFilter.includes(option.id))}
      onChange={(selected: typeof workflowStartersOptions) =>
        dispatch(setWorkflowsFilterWorkflowStarters(selected.map((option) => option.id)))
      }
      onClear={() => {
        dispatch(setWorkflowsFilterWorkflowStarters([]));
        if (!canFilterByTemplateStep(statusFilter)) {
          dispatch(cancelCurrentPerformersCounters());
          dispatch(cancelTemplateTasksCounters());
        }
      }}
      {...menuPortalProps}
    />
  );
}
