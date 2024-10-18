import * as React from 'react';
import { compose } from 'redux';

import { Tooltip } from '../UI';

import styles from './ProgressBar.css';

export enum EProgressbarColor {
  Yellow = '#FEC336',
  Red = '#E53D00',
  Grey = '#DCDCDB',
  Green = '#5FAD56',
}

export interface IProgressBarProps {
  progress: number | undefined;
  background?: string;
  color: EProgressbarColor;
  containerClassName?: string;
  tooltipContent?: React.ReactNode;
}

export const ProgressBar = ({
  progress,
  color,
  background,
  containerClassName,
  tooltipContent,
}: IProgressBarProps) => {
  const strokeWidth = progress ? `${progress}%` : '10px';

  const strokeStyle = {
    minWidth: '10px',
    width: strokeWidth,
    transition: 'width 700ms cubic-bezier(0.645, 0.045, 0.355, 1.000)', /* easeInOutCubic */
    background: color,
  };

  const renderProgressbar = () => {
    return (
      <div
        className={styles['progress-bar']}
        style={{ background }}
      >
        <div className={styles['progress-bar-stroke']} style={strokeStyle} />
      </div>
    );
  }

  const renderTooltip = (progressbar: React.ReactElement) => {
    return tooltipContent ? (
      <Tooltip content={tooltipContent} offset={[0, 4]}>
        {progressbar}
      </Tooltip>
    ) : progressbar;
  }

  const renderWrapper = (progressbar: React.ReactElement) => {
    return containerClassName ? (
      <div className={containerClassName}>
        {progressbar}
      </div>
    ) : progressbar;
  }

  return compose(renderTooltip, renderWrapper)(renderProgressbar());
};
