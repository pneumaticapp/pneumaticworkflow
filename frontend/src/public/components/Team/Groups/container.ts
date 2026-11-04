import { connect } from 'react-redux';

import { changeGroupsListSorting } from '../../../redux/actions';
import { withSyncedQueryString } from '../../../HOCs/withSyncedQueryString';
import { EGroupsListSorting } from '../../../types/user';
import { Groups, IGroupsProps } from './Groups';
import type { RootState } from '../../../redux/store';

export type TTeamProps = Pick<IGroupsProps, 'groupsListSorting'>;

export function mapStateToProps(state: RootState): TTeamProps {
  const {
    groups: { groupsListSorting },
  } = state;

  return {
    groupsListSorting,
  };
}

export const SyncedGroups = withSyncedQueryString<TTeamProps>([
  {
    propName: 'groupsListSorting',
    queryParamName: 'sorting-group',
    defaultAction: changeGroupsListSorting(EGroupsListSorting.NameAsc),
    createAction: changeGroupsListSorting,
    getQueryParamByProp: (value) => value,
  },
])(Groups);

export const GroupsContainer = connect<TTeamProps>(mapStateToProps)(SyncedGroups);
