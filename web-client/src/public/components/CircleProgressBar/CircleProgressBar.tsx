/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import styles from './CircleProgressBar.css';

export interface ICircleProgressBarProps {
  radius?: number;
  bgColor?: string;
  strokeWidth?: number;
  borderWidth?: number;
  color: string;
  percent?: number;
  text?: string;
  textClassName?: string;
}

export const CircleProgressBar = ({
  radius = 33,
  bgColor = '#ffffff',
  strokeWidth = 14,
  borderWidth = 4,
  color,
  percent = 50,
  text = '',
  textClassName,
}: ICircleProgressBarProps) => {
  const sqSize = (radius + strokeWidth / 2) * 2;
  const circumference = 2 * Math.PI * radius;
  // Примерно 10% окружности приходится на вырез снизу:
  const arc = (circumference * 90) / 100;
  // Один процент прогресса будет равен следующей длине дуги:
  const offset = arc / 100;
  const textStyles = textClassName || styles['text'];

  return (
    <div className={styles['circ-progress-bar']}>
      <svg height={sqSize} width={sqSize} viewBox={`0 0 ${sqSize} ${sqSize}`}>
        <circle
          className={styles['bg']}
          cx={sqSize / 2}
          cy={sqSize / 2}
          r={radius}
          stroke={bgColor}
          strokeWidth={strokeWidth}
          strokeDasharray={`${arc} ${circumference}`}
          fillRule="nonzero"
          fill="none"
          strokeLinecap="round"
        />
        <circle
          className={styles['progress']}
          cx={sqSize / 2}
          cy={sqSize / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth - borderWidth}
          strokeDasharray={`${offset * percent} ${circumference}`}
          fillRule="nonzero"
          fill="none"
          strokeLinecap="round"
        />
      </svg>
      <span className={textStyles}>{text}</span>
    </div>
  );
};
