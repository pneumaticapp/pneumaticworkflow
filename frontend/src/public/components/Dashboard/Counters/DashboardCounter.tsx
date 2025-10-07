/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { Link } from 'react-router-dom';
import classnames from 'classnames';
import { Tooltip } from 'reactstrap';

import { getClassNameByColor } from '../utils/getClassNameByColor';
import { TDashboardColor } from '../types';

import tooltipStyles from '../../UI/CustomTooltip/CustomTooltip.css';
import styles from './DashboardCounters.css';

export interface IDashboardCounterProps {
  isLoading?: boolean;
  counterLoader?: React.ReactNode;
  route: string | null;
  count: number | null;
  label?: string;
  color: TDashboardColor;
  className?: string;
  labelClassName?: string;
  tooltipLabel?: string;
}

const { useRef, useState } = React;

export function DashboardCounter(props: IDashboardCounterProps) {
  const { count, label, route, color, className, labelClassName, isLoading, counterLoader } = props;
  const [isShowTooltip, setIsShowTooltip] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseOver = () => {
    setIsShowTooltip(true);
  };

  const handleMouseLeave = () => {
    setIsShowTooltip(false);
  };

  const renderTooltip = () => {
    if (!containerRef.current || !props.tooltipLabel) {
      return null;
    }

    return <Tooltip
      target={containerRef.current}
      modifiers={{ preventOverflow: { boundariesElement: 'window' } }}
      autohide={false}
      delay={0}
      innerClassName={tooltipStyles['inner']}
      isOpen={isShowTooltip}
      className={classnames(
        tooltipStyles['tooltip'],
        styles['dashboard__tooltip'],
      )}
      arrowClassName={classnames(
        tooltipStyles['custom-arrow'],
        tooltipStyles['custom-arrow_bottom'],
      )}
      placement={'top'}
    >
      <p>{props.tooltipLabel}</p>
    </Tooltip>;
  };

  const renderCounterContent = () => {
    return (
      <>
        {label && <div>{label}</div>}
        <div
          className={labelClassName || styles['counter__count']}
          ref={containerRef}
        >
          {isLoading && counterLoader ? counterLoader : count}
        </div>
      </>
    );
  };

  const renderCounter = () => {
    const classNamesList = classnames(
      className,
      getClassNameByColor(color),
      count === null && styles['counter_empty'],
    );

    if (route) {
      return (
        <Link
          to={route}
          className={classNamesList}
          onMouseOver={handleMouseOver}
          onMouseLeave={handleMouseLeave}
        >
          {renderCounterContent()}
        </Link>
      );
    }

    return (
      <div
        className={classNamesList}
        onMouseOver={handleMouseOver}
        onMouseLeave={handleMouseLeave}
      >
        {renderCounterContent()}
      </div>
    );
  };

  return (
    <>
      {renderCounter()}
      {renderTooltip()}
    </>
  );
}
