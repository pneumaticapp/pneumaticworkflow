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
}

export function ExtraFieldIcon({ Icon, tooltipText, tooltipTitle, onClick }: IExtraFieldIconProps) {
  const buttonRef = React.useRef(null);

  return (
    <>
      <button
        className={styles['component-icon-container']}
        ref={buttonRef}
        onClick={onClick}
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
