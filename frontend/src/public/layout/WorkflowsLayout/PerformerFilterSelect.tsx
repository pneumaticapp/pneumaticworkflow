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
import { getGroups } from '../../redux/selectors/groups';
import { getAccountsUsers } from '../../redux/selectors/accounts';

import { getActiveUsers, getUserFullName } from '../../utils/users';
import { Avatar, FilterSelect } from '../../components/UI';
import { PerformerFilterIcon } from '../../components/icons';
import { ERenderPlaceholderType, getRenderPlaceholder } from './utils';
import { canFilterByTemplateStep } from '../../utils/workflows/filters';
import { useCheckDevice } from '../../hooks/useCheckDevice';

import styles from './WorkflowsLayout.css';

export function PerformerFilterSelect() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const { isMobile } = useCheckDevice();

  const performersGroupIdsFilter = useSelector(getWorkflowPerformersGroupsIdsFilter);
  const performersIdsFilter = useSelector(getWorkflowPerformersIdsFilter);
  const performersCounters = useSelector(getWorkflowPerformersCounters);
  const statusFilter = useSelector(getWorkflowsStatus);
  const groups: IGroup[] = useSelector(getGroups);
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
          displayName: (
            <div className={styles['user']}>
              <Avatar user={{ type: ETemplateOwnerType.UserGroup }} size="sm" />
              <span className={styles['user-name']}>{group.name}</span>
            </div>
          ),
          ...(count > 0 && { count }),
          searchByText: group.name,
        };
      }),
    [groups, performersCounters],
  );

  const activeUsers = useMemo(() => getActiveUsers(users), [users]);

  const performersOptions = React.useMemo(
    () =>
      activeUsers.map((user) => {
        const userFullName = getUserFullName(user);
        const count = performersCountersMap.get(user.id) || 0;
        return {
          ...user,
          displayName: (
            <div className={styles['user']}>
              <Avatar user={user} size="sm" />
              <span className={styles['user-name']}>{userFullName}</span>
            </div>
          ),
          ...(count > 0 && { count }),
          searchByText: userFullName,
        };
      }),
    [activeUsers, performersCounters],
  );
  const filterIds = [...performersGroupIdsFilter, ...performersIdsFilter];
  const isOneFilterId = filterIds.length === 1;
  const filterType = isOneFilterId && performersIdsFilter.length === 1 ? 'userType' : 'groupType';

  return (
    <div className={styles['performer-filter']}>
      <FilterSelect
        isDisabled={mustDisableFilter}
        isMultiple
        isSearchShown
        placeholderText={formatMessage({ id: 'workflows.filter-no-user' })}
        searchPlaceholder={formatMessage({ id: 'sorting.search-placeholder' })}
        selectedOptions={[...performersGroupIdsFilter, ...performersIdsFilter]}
        optionIdKey="id"
        optionLabelKey="displayName"
        options={[...performersGroupOptions, ...performersOptions]}
        onChange={(_, options: any) => {
          const performers = options
            .filter((item: any) => item.type === ETemplateOwnerType.User)
            .map((lItem: any) => lItem.id);
          const selectedGroups = options
            .filter((item: any) => item.type === ETemplateOwnerType.UserGroup)
            .map((lItem: any) => lItem.id);

          dispatch(setWorkflowsFilterPerfomers(performers));
          dispatch(setWorkflowsFilterPerfomersGroup(selectedGroups));
        }}
        resetFilter={() => {
          dispatch(setWorkflowsFilterPerfomers([]));
          dispatch(setWorkflowsFilterPerfomersGroup([]));
          if (!canFilterByTemplateStep(statusFilter)) {
            dispatch(cancelTemplateTasksCounters());
          }
        }}
        Icon={PerformerFilterIcon}
        renderPlaceholder={() =>
          getRenderPlaceholder({
            isDisabled: mustDisableFilter,
            filterType,
            filterIds,
            options: filterType === 'userType' ? performersOptions : performersGroupOptions,
            formatMessage,
            type: ERenderPlaceholderType.Performer,
            severalOptionPlaceholder: 'sorting.several-performers',
            defaultPlaceholder: 'sorting.all-performers',
          })
        }
        containerClassname={styles['filter-container']}
        arrowClassName={styles['header-filter__arrow']}
        positionFixed={isMobile}
      />
    </div>
  );
}
