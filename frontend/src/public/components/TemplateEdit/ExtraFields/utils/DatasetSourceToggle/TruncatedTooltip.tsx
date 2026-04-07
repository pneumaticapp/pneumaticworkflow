import * as React from 'react';
import { Tooltip } from '../../../../UI/Tooltip';
import { ITruncatedTooltipProps } from './types';
import styles from './DatasetSourceToggle.css';

export function TruncatedTooltip({ label, containerClassName, children }: ITruncatedTooltipProps) {
  if (!label) return children;

  return (
    <Tooltip 
      content={<div className={styles['dataset-source-toggle__tooltip-box']}>{label}</div>} 
      placement="top" 
      interactive={false} 
      appendTo={() => document.body}
      containerClassName={containerClassName}
    >
      {children}
    </Tooltip>
  );
}
