import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';

import { useDispatch, useSelector } from 'react-redux';
import {
  cancelTemplateTasksCounters,
  setFilterPerformers as setWorkflowsFilterPerfomers,
  setFilterPerformersGroup as setWorkflowsFilterPerfomersGroup,
} from '../../redux/workflows/slice';

import { IGroup } from '../../redux/team/types';
import { TUserListItem } from '../../types/user';
import { ETemplateOwnerType } from '../../types/template';
import { EWorkflowsStatus } from '../../types/workflow';

import {
  getWorkflowPerformersCounters,
  getWorkflowPerformersGroupsIdsFilter,
  getWorkflowPerformersIdsFilter,
  getWorkflowsStatus,
} from '../../redux/selectors/workflows';
import { getRegularGroupsList } from '../../redux/selectors/groups';
import { getAccountsUsers } from '../../redux/selectors/accounts';

import { getActiveUsers, getUserFullName } from '../../utils/users';
import { Avatar } from '../../components/UI';
import { Select } from '../../components/UI/Select';
import { PerformerFilterIcon } from '../../components/icons';
import { ERenderPlaceholderType, getRenderPlaceholder } from './utils';
import { canFilterByTemplateStep } from '../../utils/workflows/filters';
import { useMobileMenuPortalProps } from './useMobileMenuPortalProps';

import styles from './WorkflowsLayout.css';

export function PerformerFilterSelect() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const menuPortalProps = useMobileMenuPortalProps();

  const performersGroupIdsFilter = useSelector(getWorkflowPerformersGroupsIdsFilter);
  const performersIdsFilter = useSelector(getWorkflowPerformersIdsFilter);
  const performersCounters = useSelector(getWorkflowPerformersCounters);
  const statusFilter = useSelector(getWorkflowsStatus);
  const groups: IGroup[] = useSelector(getRegularGroupsList);
  const users: TUserListItem[] = useSelector(getAccountsUsers);

  const mustDisableFilter = statusFilter === EWorkflowsStatus.Snoozed || statusFilter === EWorkflowsStatus.Completed;

  const performersCountersMap = useMemo(
    () => new Map(performersCounters.map((counter) => [counter.sourceId, counter.workflowsCount])),
    [performersCounters],
  );

  const performersGroupOptions = React.useMemo(
    () =>
      groups.map((group) => {
        const count = performersCountersMap.get(group.id) || 0;
        return {
          ...group,
          type: ETemplateOwnerType.UserGroup,
          value: `${ETemplateOwnerType.UserGroup}-${group.id}`,
          label: (
            <div className={styles['user']}>
              <Avatar user={{ type: ETemplateOwnerType.UserGroup }} size="sm" />
              <span className={styles['user-name']}>{group.name}</span>
            </div>
          ),
          ...(count > 0 && { count }),
          searchByText: group.name,
        };
      }),
    [groups, performersCountersMap],
  );

  const activeUsers = useMemo(() => getActiveUsers(users), [users]);

  const performersOptions = React.useMemo(
    () =>
      activeUsers.map((user) => {
        const userFullName = getUserFullName(user);
        const count = performersCountersMap.get(user.id) || 0;
        return {
          ...user,
          type: ETemplateOwnerType.User,
          value: `${ETemplateOwnerType.User}-${user.id}`,
          label: (
            <div className={styles['user']}>
              <Avatar user={user} size="sm" />
              <span className={styles['user-name']}>{userFullName}</span>
            </div>
          ),
          ...(count > 0 && { count }),
          searchByText: userFullName,
        };
      }),
    [activeUsers, performersCountersMap],
  );
  const filterIds = [...performersGroupIdsFilter, ...performersIdsFilter];
  const isOneFilterId = filterIds.length === 1;
  const filterType = isOneFilterId && performersIdsFilter.length === 1 ? 'userType' : 'groupType';

  const options = [...performersGroupOptions, ...performersOptions];
  const selectedValues = [
    ...performersGroupIdsFilter.map((id) => `${ETemplateOwnerType.UserGroup}-${id}`),
    ...performersIdsFilter.map((id) => `${ETemplateOwnerType.User}-${id}`),
  ];

  const handleClear = () => {
    dispatch(setWorkflowsFilterPerfomers([]));
    dispatch(setWorkflowsFilterPerfomersGroup([]));
    if (!canFilterByTemplateStep(statusFilter)) {
      dispatch(cancelTemplateTasksCounters());
    }
  };

  return (
    <Select
      controlSize="sm"
      controlVariant="accent"
      Icon={PerformerFilterIcon}
      isMulti
      isSearchable
      isDisabled={mustDisableFilter}
      title={getRenderPlaceholder({
        isDisabled: mustDisableFilter,
        filterType,
        filterIds,
        options: filterType === 'userType' ? performersOptions : performersGroupOptions,
        formatMessage,
        type: ERenderPlaceholderType.Performer,
        severalOptionPlaceholder: 'sorting.several-performers',
        defaultPlaceholder: 'sorting.all-performers',
      })}
      placeholder={formatMessage({ id: 'sorting.search-placeholder' })}
      noOptionsMessage={() => formatMessage({ id: 'workflows.filter-no-user' })}
      options={options}
      value={options.filter((option) => selectedValues.includes(option.value))}
      onChange={(selected: typeof options) => {
        const getIds = (type: ETemplateOwnerType) =>
          selected.filter((option) => option.type === type).map((option) => option.id);

        dispatch(setWorkflowsFilterPerfomers(getIds(ETemplateOwnerType.User)));
        dispatch(setWorkflowsFilterPerfomersGroup(getIds(ETemplateOwnerType.UserGroup)));
      }}
      onClear={filterIds.length > 0 ? handleClear : undefined}
      {...menuPortalProps}
    />
  );
}
