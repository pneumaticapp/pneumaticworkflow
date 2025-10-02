import * as React from 'react';
import { CellProps } from 'react-table';
import { Avatar } from '../../../../../../UI';

import { UserData } from '../../../../../../UserData';
import { TableColumns } from '../../../types';
import { EXTERNAL_USER } from '../../../../../../../utils/users';

import styles from './StarterColumn.css';

type TProps = React.PropsWithChildren<CellProps<TableColumns, TableColumns['starter']>>;

export function StarterColumn({
  value: {
    workflowStarter,
    isExternal,
  }
}: TProps) {
  return (
    <UserData userId={workflowStarter}>
      {user => {
        let currentUser = user;

        if (!currentUser) {
          return null;
        }

        if (isExternal) {
          currentUser = EXTERNAL_USER;
        }

        return (
          <Avatar user={currentUser} size="sm" withTooltip containerClassName={styles['starter']} />
        )
      }}
    </UserData>
  )
}
