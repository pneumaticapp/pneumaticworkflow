/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { CustomTooltip } from '../../../UI/CustomTooltip';

import styles from '../../KickoffRedux/KickoffRedux.css';

export interface IExtraFieldIconProps {
  Icon(props: React.SVGAttributes<SVGElement>): JSX.Element;
  id: string;
  tooltipText: string;
  tooltipTitle: string;
  onClick(): void;
  disabled?: boolean;
}

export function ExtraFieldIcon({ Icon, tooltipText, tooltipTitle, onClick, disabled }: IExtraFieldIconProps) {
  const buttonRef = React.useRef(null);

  return (
    <>
      <button
        className={styles['component-icon-container']}
        ref={buttonRef}
        onClick={onClick}
        disabled={disabled}
      >
        <Icon className={styles['component-icon']} />
      </button>
      <CustomTooltip
        target={buttonRef}
        tooltipText={tooltipText}
        tooltipTitle={tooltipTitle}
      />
    </>
  );
}
