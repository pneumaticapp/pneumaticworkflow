import * as React from 'react';
import { Tooltip } from '../../../../UI/Tooltip';
import { ITruncatedTooltipProps } from './types';
import styles from './OutputFieldContent.css';

export function TruncatedTooltip({ label, containerClassName, trigger, delay, children }: ITruncatedTooltipProps) {
  if (!label) return children;

  return (
    <Tooltip 
      content={<div className={styles['output-field-content__tooltip-box']}>{label}</div>} 
      placement="top" 
      interactive={false} 
      trigger={trigger}
      delay={delay}
      appendTo={() => document.body}
      containerClassName={containerClassName}
    >
      {children}
    </Tooltip>
  );
}
