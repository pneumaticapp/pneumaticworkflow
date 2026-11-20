import React from 'react';
import type { PropsWithChildren } from 'react';
import type { CellProps } from 'react-table';
import { useDispatch } from 'react-redux';

import { setFilterTemplate as setWorkflowsFilterTemplate } from '../../../../../../../redux/workflows/slice';
import type { TTableColumns } from '../../../types';

import styles from './TemplateNameColumn.css';

type TProps = PropsWithChildren<CellProps<TTableColumns, TTableColumns['system-column-templateName']>>;

export function TemplateNameColumn({ value: { isLegacyTemplate, legacyTemplateName, template } }: TProps) {
  const dispatch = useDispatch();
  const templateName = isLegacyTemplate ? legacyTemplateName : template?.name;

  return (
    <button
      onClick={() => dispatch(setWorkflowsFilterTemplate([template?.id]))}
      type="button"
      className={styles['template-name']}
      aria-label="select this template for filtering"
    >
      {templateName}
    </button>
  );
}
