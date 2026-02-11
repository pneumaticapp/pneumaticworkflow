import React, { useRef } from 'react';
import classnames from 'classnames';
import { NumericFormat } from 'react-number-format';

import { normalizeFieldValue } from '../utils/normalizeFieldValue';
import type { IFieldInputProps, TNumericFormatRest } from './types';

import styles from '../Field.css';

export function FieldInput({
  inputClassName,
  value,
  onChange,
  type,
  placeholder,
  disabled,
  innerRef,
  shouldReplaceWithLabel = false,
  isFromConditionValueField,
  isNumericField,
  onBlur,
  onKeyDown,
  onPaste,
  icon,
  labelReplacementClassName,
  labelReplacementValue,
  rest,
}: IFieldInputProps): React.ReactElement {
  const valueString = normalizeFieldValue(value);
  const generatedIdRef = useRef(`field-input-${Math.random().toString(36).slice(2)}`);
  const inputId = rest.id ?? generatedIdRef.current;

  const restForNumeric: TNumericFormatRest = Object.fromEntries(
    Object.entries(rest).filter(([key]) => key !== 'defaultValue'),
  ) as TNumericFormatRest;

  const input = isNumericField ? (
    <NumericFormat
      value={valueString}
      onValueChange={(values) => {
        onChange({
          target: { value: values.value, name: '', type: 'text' },
        } as React.ChangeEvent<HTMLInputElement>);
      }}
      allowNegative
      decimalSeparator="."
      thousandSeparator={false}
      allowedDecimalSeparators={['.', ',']}
      getInputRef={innerRef}
      disabled={disabled}
      placeholder={placeholder}
      className={inputClassName}
      style={{
        display: shouldReplaceWithLabel ? 'none' : 'block',
        ...(isFromConditionValueField ? { width: '100%', padding: '0.8rem' } : {}),
      }}
      onBlur={onBlur}
      onKeyDown={onKeyDown}
      onPaste={onPaste}
      {...restForNumeric}
      id={inputId}
    />
  ) : (
    <input
      ref={innerRef}
      type={type}
      style={{ display: shouldReplaceWithLabel ? 'none' : 'inline' }}
      value={valueString}
      onChange={onChange}
      onBlur={onBlur}
      onKeyDown={onKeyDown}
      placeholder={placeholder}
      className={inputClassName}
      disabled={disabled}
      onPaste={onPaste}
      {...rest}
      id={inputId}
    />
  );

  if (!icon) return input;

  return (
    <div className={styles['icon-container']}>
      {shouldReplaceWithLabel && (
        <label
          htmlFor={inputId}
          className={classnames(inputClassName, labelReplacementClassName)}
        >
          {labelReplacementValue}
          &nbsp;
        </label>
      )}
      {input}
      <div className={styles['icon']}>{icon}</div>
    </div>
  );
}
