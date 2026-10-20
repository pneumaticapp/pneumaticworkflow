import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { DropdownList } from '../../components/UI';
import { getUserListSorting } from '../../redux/selectors/accounts';
import { userListSortingChanged } from '../../redux/accounts/slice';
import { userListSortingValues } from '../../constants/sortings';
import { getSortingSelectProps } from '../../utils/getSortingSelectProps';

export function UserListSorting() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const sorting = useSelector(getUserListSorting);

  return (
    <DropdownList
      controlSize="sm"
      controlVariant="accent"
      {...getSortingSelectProps(
        userListSortingValues,
        sorting,
        (value) => dispatch(userListSortingChanged(value)),
        formatMessage,
      )}
    />
  );
}
