/* eslint-disable jsx-a11y/label-has-associated-control */
import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { DateIcon } from '../../../icons';
import { TForegroundColor } from '../common/types';
import { getForegroundClass } from '../common/utils/getForegroundClass';
import { DatePicker, IDatePickerProps } from '../../form/DatePicker';

import styles from './DateField.css';
import commonStyles from '../common/styles.css';

type TInputFieldSize = 'sm' | 'md' | 'lg';

export interface IDateFieldProps extends Omit<IDatePickerProps, 'value'> {
  value: string | null;
  icon?: React.ReactNode;
  title?: string;
  fieldSize?: TInputFieldSize;
  foregroundColor?: TForegroundColor;
  errorMessage?: string;
  isRequired?: boolean;
  containerClassName?: string;
  inputRef?: React.RefObject<HTMLInputElement>;
  placeholder?: string;
  onClear?(): void;
  onChange(date: string | null): void;
  // tslint:disable-next-line: no-any
  [key: string]: any;
}

type TDateFieldProps = IDateFieldProps;

const inputContainerSizeClassMap: { [key in TInputFieldSize]: string } = {
  sm: styles['container_sm'],
  md: styles['container_md'],
  lg: styles['container_lg'],
};

export function DateField({
  icon = <DateIcon />,
  className,
  title,
  fieldSize = 'lg',
  foregroundColor = 'white',
  errorMessage,
  isRequired,
  children,
  containerClassName,
  disabled,
  placeholder,
  value,
  onChange,
  // tslint:disable-next-line: trailing-comma
  ...props
}: TDateFieldProps) {
  const { messages } = useIntl();
  const normalizedErrorMessage = errorMessage && (messages[errorMessage] || errorMessage);

  const renderInput = () => {
    const inputClassName = classnames(
      styles['input-field'],
      icon && styles['input-field_with-icon'],
      errorMessage && styles['input-field_error'],
      className,
    );

    return (
      <div className={styles['input-with-rigt-content-wrapper']}>
        <div className={inputClassName}>
          <DatePicker
            onChange={onChange}
            placeholderText={placeholder}
            selected={value}
            showPopperArrow={false}
            {...props}
          />
        </div>
        {icon && <div className={styles['icon']}>{icon}</div>}
      </div>
    );
  };

  const titleClassNames = classnames(
    styles['title'],
    getForegroundClass(foregroundColor),
    isRequired && commonStyles['title_required'],
  );

  return (
    <label
      className={classnames(
        styles['container'],
        inputContainerSizeClassMap[fieldSize],
        disabled && styles['container_disabled'],
        title && styles['container_with-title'],
        containerClassName,
      )}
    >
      {renderInput()}
      {title && <span className={titleClassNames}>{title}</span>}
      {normalizedErrorMessage && <p className={styles['error-text']}>{normalizedErrorMessage}</p>}
      {children}
    </label>
  );
}
