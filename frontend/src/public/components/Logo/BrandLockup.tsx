import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { getBrandName, getOrganizationName } from '../../constants/branding';
import { BRAND_ASSETS } from './brandAssets';
import styles from './Logo.css';

interface IBrandLockupProps extends React.SVGAttributes<SVGSVGElement> {
  variant?: 'standard' | 'wide';
  tone?: 'dark' | 'light';
}

/** A fixed logo footprint; neither the official emblem nor its composition is mirrored. */
export function BrandLockup({ variant = 'standard', tone = 'dark', className, ...props }: IBrandLockupProps) {
  const { locale } = useIntl();
  const name = getBrandName(locale);
  const organization = getOrganizationName(locale);
  const dimensions =
    variant === 'wide'
      ? { width: 210, height: 60, emblemWidth: 52, textStart: 62 }
      : { width: 170, height: 48, emblemWidth: 42, textStart: 50 };

  return (
    <svg
      width={dimensions.width}
      height={dimensions.height}
      viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={`${name} — ${organization}`}
      className={classnames(
        styles['brand-lockup'],
        styles[`brand-lockup_${variant}`],
        styles[`brand-lockup_${tone}`],
        className,
      )}
      {...props}
    >
      <image
        href={tone === 'light' ? BRAND_ASSETS.eagleWhite : BRAND_ASSETS.eagleBlack}
        width={dimensions.emblemWidth}
        height={dimensions.height}
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
      />
      <foreignObject
        x={dimensions.textStart}
        width={dimensions.width - dimensions.textStart}
        height={dimensions.height}
        aria-hidden="true"
      >
        <div className={styles['brand-copy']} dir="auto">
          <span className={styles['brand-copy__product']}>{name}</span>
          <span className={styles['brand-copy__organization']}>{organization}</span>
        </div>
      </foreignObject>
    </svg>
  );
}
