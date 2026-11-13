import React from 'react';
import { LargeLogo } from '../icons/LargeLogo';
import { LogoCircle } from '../icons/LogoCircle';
import type { ILogoProps, TMinimizedLogoSize } from './types';

import styles from './Logo.css';

export function Logo({ size, theme, partnerLogoSm, partnerLogoLg, className }: ILogoProps) {
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
          sm: 32,
          md: 40,
        };

        const sizePx = sizeToNumberMap[size as TMinimizedLogoSize];

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

        return <LogoCircle theme={theme} size={sizePx} />;
      },
    },
  ];

  return <div className={className}>{renderLogoMap.find(({ check }) => check())?.render()}</div>;
}
