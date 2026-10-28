import * as React from 'react';
import type { FormatOptionLabelMeta } from 'react-select';

import { Checkbox } from '../../Fields/Checkbox';
import type { TSelectOption } from '../types';

import styles from '../Select.css';

export function formatCompactOptionLabel(data: unknown, { context }: FormatOptionLabelMeta<unknown>) {
  const option = data as TSelectOption;
  if (context !== 'menu') return option.label;

  return (
    <span className={styles['select-sm__option']}>
      <span className={styles['select-sm__option-label']}>{option.label}</span>
      {option.count !== undefined && <span className={styles['select-sm__option-count']}>{option.count}</span>}
    </span>
  );
}

export function formatCompactMultiOptionLabel(data: unknown, meta: FormatOptionLabelMeta<unknown>) {
  const option = data as TSelectOption;
  const content = formatCompactOptionLabel(data, meta);
  if (meta.context !== 'menu' || !option.value) return content;

  return (
    <span className={styles['select-sm__option-check']}>
      <Checkbox
        checked={(meta.selectValue as TSelectOption[]).some(({ value }) => value === option.value)}
        title={content}
        onChange={() => {}}
      />
    </span>
  );
}
