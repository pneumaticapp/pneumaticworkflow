import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';

import { useDispatch, useSelector } from 'react-redux';
import { setWorkflowsFilterPerfomers, setWorkflowsFilterPerfomersGroup } from '../../redux/workflows/actions';

import { IGroup } from '../../redux/team/types';
import { IApplicationState } from '../../types/redux';
import { TUserListItem } from '../../types/user';
import { ETemplateOwnerType } from '../../types/template';
import { EWorkflowsStatus } from '../../types/workflow';

import { getActiveUsers, getUserFullName } from '../../utils/users';

import { Avatar, FilterSelect } from '../../components/UI';

import styles from './WorkflowsLayout.css';
import { PerformerFilterIcon } from '../../components/icons';
import { ERenderPlaceholderType, getRenderPlaceholder } from './utils';

export function PerformerFilterSelect() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const { performersGroupIdsFilter, performersIdsFilter } = useSelector(
    (state: IApplicationState) => state.workflows.workflowsSettings.values,
  );
  const groups: IGroup[] = useSelector((state: IApplicationState) => state.groups.list);
  const { users }: { users: TUserListItem[] } = useSelector((state: IApplicationState) => state.accounts);
  const { performersCounters } = useSelector((state: IApplicationState) => state.workflows.workflowsSettings.counters);
  const { statusFilter } = useSelector((state: IApplicationState) => state.workflows.workflowsSettings.values);
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
      />
    </div>
  );
}
