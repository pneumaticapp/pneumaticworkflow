/* eslint-disable react/no-array-index-key */
import * as React from 'react';
import classnames from 'classnames';
import { DashboardCounter, IDashboardCounterProps } from './DashboardCounter';

import styles from './DashboardCounters.css';

interface IDashboardCountersProps {
  isLoading?: boolean;
  counterLoader?: React.ReactNode;
  countersParamsList: IDashboardCounterProps[];
  className?: string;
  labelClassName?: string;
}

export const DashboardCounters = ({
  isLoading,
  counterLoader,
  countersParamsList,
  className,
  labelClassName,
}: IDashboardCountersProps) => {
  return (
    <div className={classnames(styles['counters'], className)}>
      {countersParamsList.map((counter, index) => (
        <DashboardCounter
          {...counter}
          key={index}
          labelClassName={labelClassName}
          isLoading={isLoading}
          counterLoader={counterLoader}
        />
      ))}
    </div>
  );
};
