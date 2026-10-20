import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { DropdownList } from '../../components/UI';
import { getGroupsListSorting } from '../../redux/selectors/groups';
import { changeGroupsListSorting } from '../../redux/actions';
import { groupListSortingValues } from '../../constants/sortings';
import { getSortingSelectProps } from '../../utils/getSortingSelectProps';

export function GroupListSorting() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const sorting = useSelector(getGroupsListSorting);

  return (
    <DropdownList
      controlSize="sm"
      controlVariant="accent"
      {...getSortingSelectProps(
        groupListSortingValues,
        sorting,
        (value) => dispatch(changeGroupsListSorting(value)),
        formatMessage,
      )}
    />
  );
}
