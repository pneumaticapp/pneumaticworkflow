import React from 'react';
import { useIntl } from 'react-intl';
import classNames from 'classnames';
import { CellProps } from 'react-table';

import { TaskNamesTooltipContent } from '../../../../../utils/TaskNamesTooltipContent';
import { Tooltip } from '../../../../../../UI';
import { TableColumns } from '../../../types';

import styles from './StepColumn.css';

type TProps = React.PropsWithChildren<CellProps<TableColumns, TableColumns['step']>>;

export function StepColumn({ value: { oneActiveTaskName, areMultipleTasks, namesMultipleTasks } }: TProps) {
  const { formatMessage } = useIntl();
  const namesTooltip = areMultipleTasks && TaskNamesTooltipContent(namesMultipleTasks);

  return areMultipleTasks ? (
    <Tooltip content={namesTooltip}>
      <span className={classNames(styles['step'], styles['multiple-tasks'])}>
        {formatMessage({ id: 'workflows.multiple-active-tasks' })}
      </span>
    </Tooltip>
  ) : (
    <span className={styles['step']}>{oneActiveTaskName}</span>
  );

  /**
   * TODO: Previous implementation from task 41554
   * Author: Bogdanova
   * Date: 05.29.2025
   * Description: Step display with tooltip for template name
   * Status: May be partially reused in the future
   */
  // const step = <span className={styles['step']}>{oneActiveTaskName}</span>;
  // if (!template?.name) {
  //   return step;
  // }
  // return (
  //   <Tooltip containerClassName={styles['tooltip']} content={template.name}>
  //     {step}
  //   </Tooltip>
  // );
}
