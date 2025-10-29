import * as React from 'react';
import { CellProps } from 'react-table';
import { WorkflowCardUsers } from '../../../../../../WorkflowCardUsers';
import { TableColumns } from '../../../types';
import styles from './PerformerColumns.css';

type TProps = React.PropsWithChildren<CellProps<TableColumns, TableColumns['system-column-performer']>>;

export function PerformerColumn({ value: { selectedUsers } }: TProps) {
  return (
    <div className={styles['performer-column-width']}>
      <WorkflowCardUsers users={selectedUsers} showAllUsers />
    </div>
  );
}
