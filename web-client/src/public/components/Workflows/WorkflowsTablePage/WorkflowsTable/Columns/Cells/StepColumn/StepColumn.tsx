import React from 'react';
import { CellProps } from 'react-table';

import { Tooltip } from '../../../../../../UI';
import { TableColumns } from '../../../types';

import styles from './StepColumn.css';

type TProps = React.PropsWithChildren<CellProps<TableColumns, TableColumns['step']>>;

export function StepColumn({ value: { task, template } }: TProps) {
  const step = <span className={styles['step']}>{task.name}</span>;

  if (!template?.name) {
    return step;
  }

  return (
    <Tooltip
      containerClassName={styles['tooltip']}
      content={template.name}
    >
      {step}
    </Tooltip>
  );
}
