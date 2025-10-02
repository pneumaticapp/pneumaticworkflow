/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';

import { IExtraField } from '../../types/template';

import styles from './KickoffOutputs.css';

export interface ICheckboxOutputProps extends IExtraField {}

export function CheckboxOutput({
  name,
  selections,
}: IExtraField) {
  const { formatMessage } = useIntl();

  const renderSelections = () => {
    const defaultValue = formatMessage({ id: 'template.kick-off-form-unfilled-value' });
    const mappedSelections = selections
      ?.filter(({ isSelected }) => isSelected)
      ?.reduce((acc, { value }) => [...acc, value], [])
      ?.join(', ');

    const displayValue = mappedSelections ? mappedSelections : defaultValue;

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
