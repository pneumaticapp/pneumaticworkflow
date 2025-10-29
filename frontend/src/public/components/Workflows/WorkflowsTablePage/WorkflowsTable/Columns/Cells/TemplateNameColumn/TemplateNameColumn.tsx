import React from 'react';
import { CellProps } from 'react-table';
import { TableColumns } from '../../../types';
import styles from './TemplateNameColumn.css';

type TProps = React.PropsWithChildren<CellProps<TableColumns, TableColumns['system-column-templateName']>>;

export function TemplateNameColumn({ value }: TProps) {
  return <div className={styles['template-name']}>{value.template?.name}</div>;
}
