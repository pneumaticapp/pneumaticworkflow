/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { IExtraField } from '../../types/template';

import styles from './KickoffOutputs.css';

export interface IUrlOutputProps extends IExtraField {}

export function UrlOutput({
  name,
  value,
}: IExtraField) {

  const renderValue = () => {
    const href = value as string || undefined;

    return (
      <a target="_blank" href={href} className={styles['output__url']}>
        {value as string}
      </a>
    );
  };

  return (
    <p className={styles['output']}>
      <span className={styles['output__name']}>
        {name}
      </span>
      {renderValue()}
    </p>
  );
}
