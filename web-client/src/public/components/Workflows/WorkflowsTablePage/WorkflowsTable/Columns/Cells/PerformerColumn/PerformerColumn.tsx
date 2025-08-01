import * as React from 'react';
import { CellProps } from 'react-table';
import { WorkflowCardUsers } from '../../../../../../WorkflowCardUsers';

import { TableColumns } from '../../../types';

type TProps = React.PropsWithChildren<CellProps<TableColumns, TableColumns['performer']>>;

export function PerformerColumn({ value: { selectedUsers } }: TProps) {
  return <WorkflowCardUsers users={selectedUsers} />;
}
