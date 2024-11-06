import React from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { FieldProps } from 'formik';
import PhoneInput from 'react-phone-number-input';

import { InfoIcon } from '../../icons';
import { Tooltip } from '../Tooltip';

import styles from './Phone.css';

export const Phone = ({
  field,
  form,
  tooltipText,
  showErrorIfTouched,
  errorMessage,
  title,
  ...props
}: FieldProps & IPhoneFieldProps) => {
  const [touched, setTouched] = React.useState(false);
  const { messages, formatMessage } = useIntl();
  const shouldShowErrorMessage = errorMessage && (showErrorIfTouched ? touched : true);
  const normalizedErrorMessage = shouldShowErrorMessage && (messages[errorMessage!] || errorMessage!);

  return (
    <div className={styles['phone-input']}>
      <div className={classnames(styles['phone-input__container'], shouldShowErrorMessage && styles['is-error'])}>
        <PhoneInput
          initialValueFormat="national"
          value=""
          onChange={(value) => {
            if (!form.touched[field.name]) form.setFieldTouched(field.name);
            form.setFieldValue(field.name, value);
          }}
          onBlur={() => setTouched(true)}
          {...props}
        />

        {tooltipText && (
          <div className={styles['phone-input__tooltip']}>
            <Tooltip content={formatMessage({ id: 'user.phone-tooltip' })}>
              <div>
                <InfoIcon />
              </div>
            </Tooltip>
          </div>
        )}
      </div>
      <span className={styles['phone-input__title']}>{title}</span>
      {normalizedErrorMessage && <p className={styles['phone-input__error-text']}>{normalizedErrorMessage}</p>}
    </div>
  );
};

export interface IPhoneFieldProps {
  title?: string;
  tooltipText?: string;
  errorMessage?: string;
  showErrorIfTouched?: boolean;
  isRequired?: boolean;
}
