/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';

import { IExtraField } from '../../types/template';

import styles from './KickoffOutputs.css';

export interface ICheckboxOutputProps extends IExtraField {}

export function CheckboxOutput({
  name,
  value,
}: IExtraField) {
  const { formatMessage } = useIntl();

  const renderSelections = () => {
    const defaultValue = formatMessage({ id: 'template.kick-off-form-unfilled-value' });
    const displayValue = Array.isArray(value) ? value.join(', ') : (value || defaultValue);

    return (
      <span className={styles['output__text']}>
        {displayValue}
      </span>
    );
  };

  return (
    <p className={styles['output']}>
      <span className={styles['output__name']}>
        {name}
      </span>
      {renderSelections()}
    </p>
  );
}
