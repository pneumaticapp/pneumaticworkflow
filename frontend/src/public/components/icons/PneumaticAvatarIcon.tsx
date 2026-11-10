import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { getBrandName } from '../../constants/branding';
import { BRAND_ASSETS } from '../Logo/brandAssets';
import styles from '../Logo/Logo.css';

export type TPneumaticAvatarProps = React.SVGAttributes<SVGSVGElement>;

export function PneumaticAvatarIcon({ className, ...props }: TPneumaticAvatarProps) {
  const { locale } = useIntl();

  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 32 32"
      className={classnames(styles['brand-mark'], className)}
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={getBrandName(locale)}
      {...props}
    >
      <circle cx="16" cy="16" r="16" fill="var(--pneumatic-color-black88, #002623)" />
      <image
        href={BRAND_ASSETS.eagleGold}
        x="4"
        y="4"
        width="24"
        height="24"
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
      />
    </svg>
  );
}
