import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import type { TLogoTheme } from '../Logo/Logo';
import { getBrandName, getOrganizationName } from '../../constants/branding';
import { BRAND_ASSETS } from '../Logo/brandAssets';
import styles from '../Logo/Logo.css';

export interface ILogoCircleProps {
  size?: number;
  theme?: TLogoTheme;
  className?: string;
}

export const LogoCircle = ({ size = 40, className, theme = 'dark' }: ILogoCircleProps) => {
  const { locale } = useIntl();

  return (
    <svg
      className={classnames(styles['brand-mark'], className)}
      data-testid="logo-circle"
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={`${getBrandName(locale)} — ${getOrganizationName(locale)}`}
    >
      <image
        href={theme === 'light' ? BRAND_ASSETS.eagleGold : BRAND_ASSETS.eagleBlack}
        width={size}
        height={size}
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
      />
    </svg>
  );
};
