import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { DropdownList } from '../../components/UI';
import { getTasksSettings } from '../../redux/selectors/tasks';
import { changeTaskListSorting } from '../../redux/tasks/slice';
import { processesTasksCompleteSortingValues, processesTasksSortingValues } from '../../constants/sortings';
import { ETaskListCompletionStatus } from '../../types/tasks';
import type { ETaskListCompleteSorting, ETaskListSorting } from '../../types/tasks';
import { getSortingSelectProps } from '../../utils/getSortingSelectProps';

export function TasksSorting() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const { sorting, completionStatus } = useSelector(getTasksSettings);
  const values: (ETaskListSorting | ETaskListCompleteSorting)[] =
    completionStatus === ETaskListCompletionStatus.Completed
      ? processesTasksCompleteSortingValues
      : processesTasksSortingValues;

  return (
    <DropdownList
      controlSize="sm"
      controlVariant="accent"
      {...getSortingSelectProps(values, sorting, (value) => dispatch(changeTaskListSorting(value)), formatMessage)}
    />
  );
}
