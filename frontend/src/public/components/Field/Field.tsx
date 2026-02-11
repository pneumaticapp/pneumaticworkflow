import React, { useState, useCallback } from 'react';
import classnames from 'classnames';

import { IntlMessages } from '../IntlMessages';
import { onEnterPressed, removeTrailingDotZeros } from '../../utils/handlers';
import { LexicalRichEditor } from '../RichEditor/lexical';
import { handleNumericPaste } from './utils/handleNumericPaste';
import { trackVideoEmbeddingOnPaste } from './utils/trackVideoEmbeddingOnPaste';
import { normalizeFieldValue } from './utils/normalizeFieldValue';
import { FieldInput } from './FieldInput/FieldInput';
import type { IFieldProps } from './types';
import { EFieldTagName } from './types';

import styles from './Field.css';

export type { IFieldProps };
export { EFieldTagName } from './types';

export function Field({
  labelClassName,
  labelReplacementClassName,
  labelReplacementValue,
  intlId,
  type,
  value,
  tagName = EFieldTagName.Input,
  shouldReplaceWithLabel = false,
  onChange,
  validate,
  innerRef,
  placeholder,
  errorMessage = '',
  children,
  className,
  icon,
  disabled,
  accountId,
  isNumericField,
  isFromConditionValueField,
  onKeyDown,
  autoFocus: _autoFocus,
  name = '',
  ...inputRest
}: IFieldProps): React.ReactElement {
  const [touched, setTouched] = useState(false);

  const error = errorMessage || (validate?.(value) ?? '');
  const showError = Boolean(errorMessage) || (Boolean(error) && touched);

  const setTouchedHandler = useCallback(
    (e?: React.FocusEvent<HTMLInputElement>) => {
      if (isNumericField && e?.target && 'value' in e.target && onChange) {
        removeTrailingDotZeros((e.target as { value: string }).value, onChange);
      }
      setTouched(true);
    },
    [isNumericField, onChange],
  );

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLInputElement>) => {
      onKeyDown?.(event);
      onEnterPressed(() => setTouched(true))(event);
    },
    [onKeyDown],
  );

  const handlePaste = useCallback(
    (e: React.ClipboardEvent) => {
      const text = e.clipboardData.getData('Text');
      trackVideoEmbeddingOnPaste(text);
      if (isNumericField && text.includes(',')) {
        handleNumericPaste(e, e.target as HTMLInputElement, onChange, name);
      }
    },
    [isNumericField, onChange, name],
  );

  const inputClassName = classnames(
    styles['input'],
    icon && styles['input_with-icon'],
    showError && styles['input_error'],
    className,
  );

  function renderContent(): React.ReactElement {
    switch (tagName) {
      case EFieldTagName.Textarea:
        return (
          <textarea
            className={classnames(styles['textarea'], showError && styles['textarea_error'])}
            value={normalizeFieldValue(value)}
            onChange={onChange}
            onBlur={() => setTouched(true)}
            placeholder={placeholder}
            disabled={disabled}
          />
        );
      case EFieldTagName.RichText:
        return (
          <LexicalRichEditor
            placeholder={placeholder}
            withChecklists={false}
            defaultValue={value as string}
            handleChange={(val) => {
              onChange({ target: { value: val } } as React.ChangeEvent<HTMLInputElement>);
              return Promise.resolve(val);
            }}
            className={styles['rich-editor']}
            accountId={accountId as number}
          />
        );
      default:
        return (
          <FieldInput
            inputClassName={inputClassName}
            value={value}
            onChange={onChange}
            type={type}
            placeholder={placeholder}
            disabled={disabled}
            innerRef={innerRef}
            shouldReplaceWithLabel={shouldReplaceWithLabel}
            isFromConditionValueField={isFromConditionValueField}
            isNumericField={isNumericField}
            onBlur={setTouchedHandler}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            icon={icon}
            labelReplacementClassName={labelReplacementClassName}
            labelReplacementValue={labelReplacementValue}
            rest={{ ...inputRest, name }}
          />
        );
    }
  }

  return (
    <div className={labelClassName}>
      {renderContent()}
      {intlId && <IntlMessages id={intlId} />}
      {showError && (
        <p className={styles['field__error-text']}>
          <IntlMessages id={error} />
        </p>
      )}
      {children}
    </div>
  );
}
