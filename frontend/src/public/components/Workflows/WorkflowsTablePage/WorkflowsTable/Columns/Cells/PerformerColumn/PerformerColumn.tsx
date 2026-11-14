import React, { useCallback } from 'react';
import type { PropsWithChildren } from 'react';

import { useDispatch } from 'react-redux';
import type { CellProps } from 'react-table';

import { WorkflowCardUsers } from '../../../../../../WorkflowCardUsers';
import { setFilterPerformers, setFilterPerformersGroup } from '../../../../../../../redux/workflows/slice';
import type { TTableColumns } from '../../../types';

import styles from './PerformerColumns.css';

type TProps = PropsWithChildren<CellProps<TTableColumns, TTableColumns['system-column-performer']>>;

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
