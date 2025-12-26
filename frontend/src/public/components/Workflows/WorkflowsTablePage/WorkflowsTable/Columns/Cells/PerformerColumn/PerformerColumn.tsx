import * as React from 'react';
import { useCallback } from 'react';
import { useDispatch } from 'react-redux';
import { CellProps } from 'react-table';

import { WorkflowCardUsers } from '../../../../../../WorkflowCardUsers';
import { setFilterPerformers, setFilterPerformersGroup } from '../../../../../../../redux/workflows/slice';
import { TableColumns } from '../../../types';

import styles from './PerformerColumns.css';

type TProps = React.PropsWithChildren<CellProps<TableColumns, TableColumns['system-column-performer']>>;

export function PerformerColumn({ value: { selectedUsers } }: TProps) {
  const dispatch = useDispatch();

  const applyFilterPerformer = useCallback(
    (performerIds: number[], groupIds: number[]) => {
      dispatch(setFilterPerformers(performerIds));
      dispatch(setFilterPerformersGroup(groupIds));
    },
    [dispatch],
  );

  return (
    <div className={styles['performer-column-width']}>
      <WorkflowCardUsers users={selectedUsers} showAllUsers applyFilterPerformer={applyFilterPerformer} />
    </div>
  );
}
