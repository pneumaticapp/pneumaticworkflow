import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { Select } from '../../components/UI';
import { getTasksSettings } from '../../redux/selectors/tasks';
import { changeTaskListSorting } from '../../redux/tasks/slice';
import { processesTasksCompleteSortingValues, processesTasksSortingValues } from '../../constants/sortings';
import { ETaskListCompletionStatus } from '../../types/tasks';
import type { ETaskListCompleteSorting, ETaskListSorting } from '../../types/tasks';
import { getEnumSelectProps } from '../../utils/getEnumSelectProps';

export function TasksSorting() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const { sorting, completionStatus } = useSelector(getTasksSettings);
  const values: (ETaskListSorting | ETaskListCompleteSorting)[] =
    completionStatus === ETaskListCompletionStatus.Completed
      ? processesTasksCompleteSortingValues
      : processesTasksSortingValues;

  return (
    <Select
      controlSize="sm"
      controlVariant="accent"
      {...getEnumSelectProps(values, sorting, (value) => dispatch(changeTaskListSorting(value)), formatMessage)}
    />
  );
}
