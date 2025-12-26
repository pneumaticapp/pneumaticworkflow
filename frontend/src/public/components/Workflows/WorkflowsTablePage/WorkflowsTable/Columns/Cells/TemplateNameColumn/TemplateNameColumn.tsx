import React from 'react';
import { CellProps } from 'react-table';
import { useDispatch } from 'react-redux';

import { setFilterTemplate as setWorkflowsFilterTemplate } from '../../../../../../../redux/workflows/slice';
import { TableColumns } from '../../../types';

import styles from './TemplateNameColumn.css';

type TProps = React.PropsWithChildren<CellProps<TableColumns, TableColumns['system-column-templateName']>>;

export function TemplateNameColumn({ value }: TProps) {
  const dispatch = useDispatch();

  return (
    <button
      onClick={() => dispatch(setWorkflowsFilterTemplate([value.template?.id]))}
      type="button"
      className={styles['template-name']}
      aria-label="select this template for filtering"
    >
      {value.template?.name}
    </button>
  );
}
