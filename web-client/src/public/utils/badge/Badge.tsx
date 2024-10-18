/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { CustomTooltip } from '../../components/UI/CustomTooltip';

import styles from './Badge.css';

export interface IVariableProps {
  title: React.ReactNode;
  subtitle?: string;
  fontSize?: string;
  className?: string;
}

export const Badge = ({
  title,
  subtitle,
  fontSize,
  className,
}: IVariableProps) => {
  const tooltipTargetRef = React.useRef(null);

  return (
    <span
      className={classnames(className, styles['badge'], styles['specifity'])}
      ref={tooltipTargetRef}
      style={{ fontSize }}
    >
      {title}
      {subtitle && (
        <CustomTooltip
          target={tooltipTargetRef}
          tooltipText={subtitle}
        />
      )}
    </span>
  );
};
