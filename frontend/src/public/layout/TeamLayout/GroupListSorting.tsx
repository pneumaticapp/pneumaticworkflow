import React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { Select } from '../../components/UI';
import { getGroupsListSorting } from '../../redux/selectors/groups';
import { changeGroupsListSorting } from '../../redux/actions';
import { groupListSortingValues } from '../../constants/sortings';
import { getEnumSelectProps } from '../../utils/getEnumSelectProps';

export function GroupListSorting() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const sorting = useSelector(getGroupsListSorting);

  return (
    <Select
      controlSize="sm"
      controlVariant="accent"
      {...getEnumSelectProps(
        groupListSortingValues,
        sorting,
        (value) => dispatch(changeGroupsListSorting(value)),
        formatMessage,
      )}
    />
  );
}
