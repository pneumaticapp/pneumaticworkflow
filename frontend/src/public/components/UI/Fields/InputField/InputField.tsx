/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { FieldHookConfig, useField } from 'formik';

import { TForegroundColor } from '../common/types';
import { getForegroundClass } from '../common/utils/getForegroundClass';
import { EyeIcon, RoundClearIconLg, RoundClearIconMd, RoundClearIconSm } from '../../../icons';
import { EColors } from '../../../../constants/defaultValues';

import styles from './InputField.css';
import commonStyles from '../common/styles.css';

type TInputFieldSize = 'sm' | 'md' | 'lg';

export interface IInputFieldProps {
  icon?: React.ReactNode;
  title?: string;
  fieldSize?: TInputFieldSize;
  foregroundColor?: TForegroundColor;
  errorMessage?: string;
  showErrorIfTouched?: boolean;
  isRequired?: boolean;
  containerClassName?: string;
  inputRef?: React.RefObject<HTMLInputElement>;
  showPasswordVisibilityToggle?: boolean;
  onClear?(): void;
  // tslint:disable-next-line: no-any
  [key: string]: any;
}

type TInputFieldProps = IInputFieldProps & React.HTMLProps<HTMLInputElement>;

const inputContainerSizeClassMap: { [key in TInputFieldSize]: string } = {
  sm: styles['container_sm'],
  md: styles['container_md'],
  lg: styles['container_lg'],
};

export function InputField({
  type = 'text',
  icon,
  ref,
  inputRef: inputRefProp,
  className,
  title,
  fieldSize = 'lg',
  foregroundColor = 'white',
  errorMessage,
  isRequired,
  children,
  containerClassName,
  disabled,
  onClear,
  value,
  showErrorIfTouched = false,
  showPasswordVisibilityToggle = false,
  // tslint:disable-next-line: trailing-comma
  ...props
}: TInputFieldProps) {
  const [touched, setTouched] = React.useState(false);
  const [isPasswordVisible, setIsPasswordVisible] = React.useState(false);
  const { messages, formatMessage } = useIntl();
  const inputRef = inputRefProp || React.useRef(null);
  const shouldShowErrorMessage = errorMessage && (showErrorIfTouched ? touched : true);
  const normalizedErrorMessage = shouldShowErrorMessage && (messages[errorMessage!] || errorMessage!);

  const renderInput = () => {
    const inputClassName = classnames(
      styles['input-field'],
      icon && styles['input-field_with-icon'],
      onClear && styles['input-field_with-clearing'],
      shouldShowErrorMessage && styles['input-field_error'],
      className,
    );

    const getInputType = () => {
      if (!showPasswordVisibilityToggle) {
        return type;
      }

      return isPasswordVisible ? 'text' : 'password';
    };

    const input = (
      <input
        value={value}
        ref={inputRef}
        type={getInputType()}
        className={inputClassName}
        disabled={disabled}
        data-testid="input-field"
        onBlur={() => setTouched(true)}
        {...props}
      />
    );

    const renderRightContent = () => {
      if (onClear) {
        return renderClearButton();
      }

      if (showPasswordVisibilityToggle) {
        return (
          <div
            onClick={() => setIsPasswordVisible((prev) => !prev)}
            className={styles['password-toggle']}
            role="button"
          >
            <EyeIcon fill={isPasswordVisible ? EColors.Primary : EColors.Black16} />
          </div>
        );
      }

      if (icon) {
        return <div className={styles['icon']}>{icon}</div>;
      }

      return null;
    };

    const renderClearButton = () => {
      if (!value) {
        return null;
      }

      const iconMap: { [key in TInputFieldSize]: React.ReactNode } = {
        sm: <RoundClearIconSm />,
        md: <RoundClearIconMd />,
        lg: <RoundClearIconLg />,
      };

      return (
        <button
          type="button"
          onClick={onClear}
          className={styles['clear-button']}
          aria-label={formatMessage({ id: 'ui-input.clear' })}
          data-testid="clear-button"
        >
          {iconMap[fieldSize]}
        </button>
      );
    };

    return (
      <div className={styles['input-with-rigt-content-wrapper']}>
        {input}

        {renderRightContent()}
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

export function FormikInputField(props: TInputFieldProps & FieldHookConfig<string>) {
  const [field, meta] = useField(props);

  return (
    <InputField
      {...props}
      {...field}
      {...(meta.touched && meta.error && props.type !== 'hidden' && { errorMessage: meta.error })}
    />
  );
}
