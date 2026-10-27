import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { Select } from '../../components/UI';
import { getUserListSorting } from '../../redux/selectors/accounts';
import { userListSortingChanged } from '../../redux/accounts/slice';
import { userListSortingValues } from '../../constants/sortings';
import { getSortingSelectProps } from '../../utils/getSortingSelectProps';

export function UserListSorting() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const sorting = useSelector(getUserListSorting);

  return (
    <Select
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
