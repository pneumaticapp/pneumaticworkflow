import React, { PropsWithChildren } from 'react';
import { useDispatch } from 'react-redux';
import { useIntl } from 'react-intl';
import classNames from 'classnames';
import { CellProps } from 'react-table';

import { setFilterTemplateTasks } from '../../../../../../../redux/workflows/slice';
import { TaskNamesTooltipContent } from '../../../../../utils/TaskNamesTooltipContent';
import { Tooltip } from '../../../../../../UI';
import { TableColumns } from '../../../types';

import styles from './TaskColumn.css';

type TProps = PropsWithChildren<CellProps<TableColumns, TableColumns['system-column-step']>>;

export function TaskColumn({ value: { oneActiveTaskName, areMultipleTasks, multipleTasksNamesByApiNames } }: TProps) {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();

  const namesTooltip = areMultipleTasks && TaskNamesTooltipContent(multipleTasksNamesByApiNames);
  const singleActiveTaskApiName = Object.keys(multipleTasksNamesByApiNames)[0];

  return areMultipleTasks ? (
    <Tooltip content={namesTooltip}>
      <span className={classNames(styles['task'], styles['multiple-tasks'])}>
        {formatMessage({ id: 'workflows.multiple-active-tasks' })}
      </span>
    </Tooltip>
  ) : (
    <button
      onClick={() => dispatch(setFilterTemplateTasks([singleActiveTaskApiName]))}
      type="button"
      aria-label="select this task for filtering"
      className={styles['single-task_button']}
    >
      <span className={classNames(styles['task'], styles['single-task'])}>{oneActiveTaskName}</span>
    </button>
  );
}
