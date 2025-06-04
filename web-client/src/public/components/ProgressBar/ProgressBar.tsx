import React, { ReactElement, ReactNode } from 'react';

import { Tooltip } from '../UI';
import { ProgressBarGrid } from './ProgressBarGrid';
import { IWorkflowTaskItem } from '../../types/workflow';

import styles from './ProgressBar.css';

export enum EProgressbarColor {
  Yellow = '#FFC107',
  Red = '#E53D00',
  Grey = '#979795',
  Green = '#5FAD56',
}

export interface IProgressBarProps {
  tasks?: IWorkflowTaskItem[];
  progress: number | undefined;
  background?: string;
  color: EProgressbarColor;
  containerClassName?: string;
  tooltipContent?: ReactNode;
}

export const ProgressBar = ({
  progress,
  color,
  background,
  containerClassName,
  tooltipContent,
  tasks,
}: IProgressBarProps) => {
  const strokeWidth = progress ? `${progress}%` : '10px';

  const strokeStyle = {
    minWidth: '10px',
    width: strokeWidth,
    transition: 'width 700ms cubic-bezier(0.645, 0.045, 0.355, 1.000)' /* easeInOutCubic */,
    background: color,
  };

  const renderWrapper = () => {
    return containerClassName ? (
      <div className={containerClassName}>
        <ProgressBarGrid tasks={tasks || []} />
      </div>
    ) : (
      <div className={styles['progress-bar']} style={{ background }}>
        <div className={styles['progress-bar-stroke']} style={strokeStyle} />
      </div>
    );
  };

  const renderTooltip = (progressbar: ReactElement) => {
    return tooltipContent && !containerClassName ? (
      <Tooltip content={tooltipContent} offset={[0, 4]}>
        {progressbar}
      </Tooltip>
    ) : (
      progressbar
    );
  };

  const withWrapper = renderWrapper();
  const withTooltip = renderTooltip(withWrapper);

  return withTooltip;
};
