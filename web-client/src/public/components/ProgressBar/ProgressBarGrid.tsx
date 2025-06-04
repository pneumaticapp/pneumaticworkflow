import React, { CSSProperties } from 'react';
import { Tooltip } from '../UI';
import { IWorkflowTaskItem } from '../../types/workflow';
import styles from './ProgressBar.css';

export const ProgressBarGrid = ({ tasks }: { tasks: IWorkflowTaskItem[] }) => {
  return (
    <div className={styles['container-bar-grid']}>
      {tasks.length > 0 &&
        tasks.map(({ name, color }) => (
          <Tooltip content={name} containerClassName={styles['tooltip-classname']} key={name}>
            <div className={styles['progress-step']} style={{ '--progress-step-color': color } as CSSProperties} />
          </Tooltip>
        ))}
      {tasks.length === 0 && <div className={styles['progress-all-steps-skipped']} />}
    </div>
  );
};
