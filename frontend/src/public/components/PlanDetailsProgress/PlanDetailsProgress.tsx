/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import styles from './PlanDetailsProgress.css';

import { CircleProgressBar } from '../CircleProgressBar';

import { calculateProgressColor } from '../../utils/helpers';
import { capitalize } from '../../utils/strings';

export interface IPlanDetailsProgress {
  value?: number | null;
  limit?: number | null;
  units?: string;
  color?: string;
  className?: string;
}

export class PlanDetailsProgress extends React.Component<IPlanDetailsProgress> {
  private  getPercentage() {
    const { value, limit } = this.props;

    if (Number.isFinite(value as number) && limit) {
      return Math.min(Math.trunc((value as number / limit) * 100), 100);
    }

    return undefined;
  }
  public render() {
    const { value, limit, units, color } = this.props;
    const percentage = this.getPercentage();

    if (percentage === undefined) {
      return null;
    }

    const progressColor = calculateProgressColor(percentage);
    const normalizedLimit = limit === Infinity ? 'unlimited' : value;

    return (
      <div className={styles['plan-details-progress']}>
        <CircleProgressBar
          strokeWidth={18}
          borderWidth={6}
          color={color || progressColor}
          percent={percentage}
          text={`${value} of ${normalizedLimit} ${capitalize(units)}`}
          textClassName={styles['plan-details-progress-text']}
          radius={54}
        />
      </div>
    );
  }
}
