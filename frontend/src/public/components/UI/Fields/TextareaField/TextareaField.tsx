import * as React from 'react';
import { useRef, useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import type { FieldHookConfig } from 'formik';
import { useField } from 'formik';

import type { TForegroundColor } from '../common/types';
import { getForegroundClass } from '../common/utils/getForegroundClass';

import styles from './TextareaField.css';
import commonStyles from '../common/styles.css';

export interface ITextareaFieldProps {
  title?: string;
  foregroundColor?: TForegroundColor;
  errorMessage?: string;
  showErrorIfTouched?: boolean;
  isRequired?: boolean;
  containerClassName?: string;
  textareaRef?: React.RefObject<HTMLTextAreaElement>;
}

type TTextareaFieldProps = ITextareaFieldProps & React.HTMLProps<HTMLTextAreaElement>;

export function TextareaField({
  title,
  foregroundColor = 'white',
  errorMessage,
  isRequired,
  containerClassName,
  className,
  disabled,
  textareaRef,
  showErrorIfTouched = false,
  ...props
}: TTextareaFieldProps) {
  const [touched, setTouched] = useState(false);
  const { messages } = useIntl();
  const textareaIdRef = useRef<string | null>(null);

  if (!textareaIdRef.current) {
    textareaIdRef.current = `textarea-${Math.random().toString(36).slice(2, 9)}`;
  }
  const textareaId = textareaIdRef.current;

  const shouldShowErrorMessage = errorMessage && (showErrorIfTouched ? touched : true);
  const normalizedErrorMessage = shouldShowErrorMessage && (messages[errorMessage!] || errorMessage!);

  const titleClassNames = classnames(
    styles['title'],
    getForegroundClass(foregroundColor),
    isRequired && commonStyles['title_required'],
  );

  return (
    <label
      htmlFor={textareaId}
      className={classnames(
        styles['container'],
        disabled && styles['container_disabled'],
        title && styles['container_with-title'],
        containerClassName,
      )}
    >
      <textarea
        id={textareaId}
        ref={textareaRef}
        disabled={disabled}
        className={classnames(styles['textarea'], shouldShowErrorMessage && styles['textarea_error'], className)}
        data-testid="textarea-field"
        onBlur={() => setTouched(true)}
        {...props}
      />
      {title && <span className={titleClassNames}>{title}</span>}
      {normalizedErrorMessage && <p className={styles['error-text']}>{normalizedErrorMessage}</p>}
    </label>
  );
}

export function FormikTextareaField(props: TTextareaFieldProps & FieldHookConfig<string>) {
  const [field, meta] = useField(props);

  return <TextareaField {...props} {...field} {...(meta.touched && meta.error && { errorMessage: meta.error })} />;
}
