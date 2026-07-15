import React from 'react';

import { ExtraFieldsLabels } from '../ExtraFields/utils/ExtraFieldsLabels';
import { isArrayWithItems } from '../../../utils/helpers';
import { IKickoffLabelsProps } from './types';

import styles from './KickoffRedux.css';

export function KickoffLabels({ fields, onToggle }: IKickoffLabelsProps) {
  if (!isArrayWithItems(fields)) return null;

  return (
    <div
      className={styles['description__short']}
      onClick={onToggle}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onToggle();
        }
      }}
      tabIndex={0}
      role="button"
      aria-label="Toggle expand"
    >
      <ExtraFieldsLabels extraFields={fields} />
    </div>
  );
}
