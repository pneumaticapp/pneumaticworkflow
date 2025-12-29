import React, { PropsWithChildren } from 'react';
import { CellProps } from 'react-table';
import { useDispatch } from 'react-redux';

import { setFilterWorkflowStarters as setWorkflowsFilterWorkflowStarters } from '../../../../../../../redux/workflows/slice';
import { UserData } from '../../../../../../UserData';
import { EXTERNAL_USER } from '../../../../../../../utils/users';
import { Avatar } from '../../../../../../UI';

import { TableColumns } from '../../../types';
import styles from './StarterColumn.css';

type TProps = PropsWithChildren<CellProps<TableColumns, TableColumns['system-column-starter']>>;

export function StarterColumn({ value: { workflowStarter, isExternal } }: TProps) {
  const dispatch = useDispatch();

  return (
    <UserData userId={workflowStarter}>
      {(user) => {
        let currentUser = user;

        if (!currentUser) {
          return null;
        }

        if (isExternal) {
          currentUser = EXTERNAL_USER;
        }

        return (
          <div className={styles['starter-column']}>
            <button
              onClick={() => dispatch(setWorkflowsFilterWorkflowStarters([currentUser.id]))}
              type="button"
              aria-label="select this starter for filtering"
            >
              <Avatar user={currentUser} size="sm" withTooltip />
            </button>
          </div>
        );
      }}
    </UserData>
  );
}
