import * as React from 'react';
import { LargeLogo, LogoCircle } from '../icons';

import styles from './Logo.css';

export type TLogoTheme = 'dark' | 'light';
export type TLogoSize = 'sm' | 'md' | 'lg';
export type TMinimizedLogoSize = 'sm' | 'md';
export type TExtendedLogoSize = 'lg';

export interface ILogoProps {
  size: TLogoSize;
  theme: TLogoTheme;
  partnerLogoSm: string | null;
  partnerLogoLg: string | null;
  className?: string;
}

export function Logo({
  size,
  theme,
  partnerLogoSm,
  partnerLogoLg,
  className,
}: ILogoProps) {
  const renderLogoMap = [
    {
      check: () => size === 'lg' && partnerLogoLg,
      render: () => <img src={partnerLogoLg!} alt="Logo" />,
    },
    {
      check: () => size === 'lg',
      render: () => <LargeLogo />,
    },
    {
      check: () => true,
      render: () => {
        const sizeToNumberMap = {
          'sm': 32,
          'md': 40,
        }

        const sizePx = sizeToNumberMap[size as TMinimizedLogoSize]

        if (partnerLogoSm) {
          return (
            <img
              width={sizePx}
              height={sizePx}
              src={partnerLogoSm}
              alt="Logo"
              className={styles['partner-small-logo']}
            />
          );
        }

        return <LogoCircle theme={theme} size={sizePx} />
      },
    },
  ]

  return (
    <div className={className}>
      {renderLogoMap.find(({ check }) => check())?.render()}
    </div>
  );
}
