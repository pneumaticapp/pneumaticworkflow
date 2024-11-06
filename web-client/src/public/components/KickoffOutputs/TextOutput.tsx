import * as React from 'react';

import { RichText } from '../RichText';
import { IExtraField } from '../../types/template';

import styles from './KickoffOutputs.css';

export interface ITextOutputProps extends IExtraField {}

export function TextOutput({ name, value }: IExtraField) {
  const renderValue = () => {
    return (
      <span className={styles['output__text']}>
        <RichText text={value as string} />
      </span>
    );
  };

  return (
    <p className={styles['output']}>
      <span className={styles['output__name']}>{name}</span>
      <span className={styles['output__text']}>{renderValue()}</span>
    </p>
  );
}
