import React, { PropsWithChildren } from 'react';
import { CellProps } from 'react-table';
import { useDispatch } from 'react-redux';
import { useIntl } from 'react-intl';

import { setFilterTemplate as setWorkflowsFilterTemplate } from '../../../../../../../redux/workflows/slice';
import { TableColumns } from '../../../types';

import styles from './TemplateNameColumn.css';

type TProps = PropsWithChildren<CellProps<TableColumns, TableColumns['system-column-templateName']>>;

export function TemplateNameColumn({ value: { isLegacyTemplate, legacyTemplateName, template } }: TProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const templateName = isLegacyTemplate ? legacyTemplateName : template?.name;

  return (
    <button
      onClick={() => dispatch(setWorkflowsFilterTemplate([template?.id]))}
      type="button"
      className={styles['template-name']}
      aria-label={formatMessage({ id: 'workflows.filter-select-template' })}
    >
      {templateName}
    </button>
  );
}
