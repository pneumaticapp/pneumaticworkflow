import React from 'react';
import classnames from 'classnames';

import styles from './Loader.css';

export type TSpinnerColor = 'yellow' | 'white' | 'black';

export interface ILoaderProps {
  containerClassName?: string;
  isLoading?: boolean;
  spinnerColor?: TSpinnerColor;
  isCentered?: boolean;
}

export function Loader({ containerClassName, isLoading, isCentered = true, spinnerColor = 'black' }: ILoaderProps) {
  if (!isLoading) {
    return null;
  }

  const spinnerColorClassMap: { [key in TSpinnerColor]: string } = {
    white: styles['spinner_white'],
    yellow: styles['spinner_yellow'],
    black: styles['spinner_black'],
  };

  return (
    <div className={classnames(isCentered && styles['loader-container'], containerClassName)}>
      <div className={classnames(styles['spinner'], spinnerColorClassMap[spinnerColor])}>
        <div></div>
        <div></div>
        <div></div>
        <div></div>
        <div></div>
        <div></div>
        <div></div>
        <div></div>
        <div></div>
        <div></div>
        <div></div>
        <div></div>
      </div>
    </div>
  );
}
