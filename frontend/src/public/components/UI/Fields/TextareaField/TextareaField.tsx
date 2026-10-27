import * as React from 'react';
import { useRef } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import type { FieldHookConfig } from 'formik';
import { useField } from 'formik';

import styles from './TextareaField.css';
import commonStyles from '../common/styles.css';

export interface ITextareaFieldProps {
  title?: string;
  errorMessage?: string;
  isRequired?: boolean;
}

type TTextareaFieldProps = ITextareaFieldProps & React.HTMLProps<HTMLTextAreaElement>;

export function TextareaField({ title, errorMessage, isRequired, className, disabled, ...props }: TTextareaFieldProps) {
  const { messages } = useIntl();
  const textareaIdRef = useRef<string | null>(null);

  if (!textareaIdRef.current) {
    textareaIdRef.current = `textarea-${Math.random().toString(36).slice(2, 9)}`;
  }
  const textareaId = textareaIdRef.current;

  const normalizedErrorMessage = errorMessage && (messages[errorMessage] || errorMessage);

  const titleClassNames = classnames(
    styles['title'],
    commonStyles['title_foreground-white'],
    isRequired && commonStyles['title_required'],
  );

  return (
    <label
      htmlFor={textareaId}
      className={classnames(
        styles['container'],
        disabled && styles['container_disabled'],
        title && styles['container_with-title'],
      )}
    >
      <textarea
        id={textareaId}
        disabled={disabled}
        className={classnames(styles['textarea'], errorMessage && styles['textarea_error'], className)}
        data-testid="textarea-field"
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
