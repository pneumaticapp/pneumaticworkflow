/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';
import { Input, InputProps } from 'reactstrap';
import { NumericFormat } from 'react-number-format';

import { IntlMessages } from '../IntlMessages';
import { onEnterPressed, removeTrailingDotZeros } from '../../utils/handlers';

import { RichEditor } from '../RichEditor';
import { trackVideoEmbedding } from '../../utils/analytics';

import { youtubeVideoRegexp, loomVideoRegexp, wistiaVideoRegexp } from '../../constants/defaultValues';

import styles from './Field.css';

export interface IFieldProps extends InputProps {
  labelClassName?: string;
  labelReplacementClassName?: string;
  labelReplacementValue?: string;
  icon?: React.ReactNode;
  intlId?: string;
  tagName?: EFieldTagName;
  shouldReplaceWithLabel?: boolean;
  onChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void;
  validate?(value: InputProps['value']): string;
  errorMessage?: string;
  accountId?: number;
  onKeyDown?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  isNumericField?: boolean;
  isFromConditionValueField?: boolean;
}

export interface IFieldState {
  touched: boolean;
}

export enum EFieldTagName {
  Input = 'input',
  Textarea = 'textarea',
  RichText = 'RichText',
}

export class Field extends React.PureComponent<IFieldProps, IFieldState> {
  public state = {
    touched: false,
  };

  public render() {
    const {
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
      autoFocus,
      accountId,
      isNumericField,
      isFromConditionValueField,
      // tslint:disable-next-line: trailing-comma
      ...rest
    } = this.props;
    const { touched } = this.state;

    const error = errorMessage || (validate && validate(value)) || '';

    const shouldShowErrorMessage = Boolean(errorMessage) || (Boolean(error) && touched);

    const renderInput = () => {
      const inputClassName = classnames(
        styles['input'],
        icon && styles['input_with-icon'],
        shouldShowErrorMessage && styles['input_error'],
        className,
      );

      const handlePasteText = (e: React.ClipboardEvent) => {
        const text = e.clipboardData.getData('Text');

        if (text.match(wistiaVideoRegexp)?.[0]) {
          trackVideoEmbedding('Wistia');
        }

        if (text.match(youtubeVideoRegexp)?.[0]) {
          trackVideoEmbedding('YouTube');
        }

        if (text.match(loomVideoRegexp)?.[0]) {
          trackVideoEmbedding('Loom');
        }

        if (isNumericField && text.includes(',')) {
          // !when working with this condition there is a flickering with an error in the validation line
          e.preventDefault();

          const input = e.target as HTMLInputElement;
          const currentValue = input.value;
          const selStart = input.selectionStart || 0;
          const selEnd = input.selectionEnd || 0;

          let firstSeparatorIndex = text.indexOf(',');
          const firstDotIndex = text.indexOf('.');
          if (firstDotIndex !== -1 && firstDotIndex < firstSeparatorIndex) {
            firstSeparatorIndex = firstDotIndex;
          }
          const processedText =
            text.substring(0, firstSeparatorIndex) + '.' + text.substring(firstSeparatorIndex + 1).replace(/,/g, '');

          const hasDecimalSeparator = currentValue.includes('.');
          const decimalPosition = currentValue.indexOf('.');
          let newValue = '';
          if (hasDecimalSeparator && selStart <= decimalPosition) {
            newValue =
              currentValue.substring(0, selStart) + processedText + currentValue.substring(selEnd).replace(/\./g, '');
          } else if (!hasDecimalSeparator) {
            newValue = currentValue.substring(0, selStart) + processedText + currentValue.substring(selEnd);
          } else {
            newValue = currentValue.substring(0, selStart) + text + currentValue.substring(selEnd);
          }

          onChange({
            target: {
              value: newValue,
              name: rest.name || '',
              type: 'text',
            },
          } as React.ChangeEvent<HTMLInputElement>);
        }
      };

      const { defaultValue, ...restProps } = rest;
      const input = isNumericField ? (
        <NumericFormat
          value={Array.isArray(value) ? value.join('') : (value as string | number | undefined)}
          onValueChange={(values) => {
            onChange({
              target: {
                value: values.value,
                name: '',
                type: 'text',
              },
            } as React.ChangeEvent<HTMLInputElement>);
          }}
          allowNegative={true}
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
          onBlur={this.setTouched}
          onKeyDown={this.handleKeyDown}
          autoFocus={autoFocus}
          onPaste={handlePasteText}
          {...restProps}
        />
      ) : (
        <Input
          innerRef={innerRef}
          type={type}
          style={{
            /* stylelint-disable-next-line */
            display: shouldReplaceWithLabel ? 'none' : 'inline',
          }}
          value={value}
          onChange={onChange}
          onBlur={this.setTouched}
          onKeyDown={this.handleKeyDown}
          placeholder={placeholder}
          className={inputClassName}
          disabled={disabled}
          autoFocus={autoFocus}
          onPaste={handlePasteText}
          {...rest}
        />
      );

      const label = (
        <label className={classnames(inputClassName, labelReplacementClassName)}>
          {labelReplacementValue}
          &nbsp;
        </label>
      );

      if (!icon) {
        return input;
      }

      return (
        <div className={styles['icon-container']}>
          {shouldReplaceWithLabel && label}
          {input}
          <div className={styles['icon']}>{icon}</div>
        </div>
      );
    };

    const renderTextarea = () => (
      <textarea
        className={classnames(styles['textarea'], shouldShowErrorMessage && styles['textarea_error'])}
        value={value}
        onChange={onChange}
        onBlur={this.setTouched}
        placeholder={placeholder}
        disabled={disabled}
        autoFocus={autoFocus}
      />
    );

    const renderRichEditor = () => (
      <RichEditor
        placeholder={placeholder}
        defaultValue={value as string}
        handleChange={(value) => {
          onChange({ target: { value } } as React.ChangeEvent<HTMLInputElement>);

          return Promise.resolve(value);
        }}
        className={styles['rich-editor']}
        accountId={accountId as number}
      />
    );

    const INPUT_TYPE_MAP = {
      [EFieldTagName.Input]: renderInput(),
      [EFieldTagName.Textarea]: renderTextarea(),
      [EFieldTagName.RichText]: renderRichEditor(),
    };

    return (
      <div className={labelClassName}>
        {INPUT_TYPE_MAP[tagName]}
        {intlId && <IntlMessages id={intlId} />}
        {shouldShowErrorMessage && (
          <p className={styles['field__error-text']}>
            <IntlMessages id={error} />
          </p>
        )}
        {children}
      </div>
    );
  }

  private handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    const { onKeyDown } = this.props;

    if (onKeyDown) {
      onKeyDown(event);
    }

    onEnterPressed(this.setTouched)(event);
  };

  private setTouched = (e?: React.FocusEvent<Element>) => {
    if (this.props.isNumericField && e?.target && 'value' in e.target && this.props.onChange) {
      const target = e.target as { value: string };
      removeTrailingDotZeros(target.value, this.props.onChange);
    }
    this.setState({ touched: true });
  };
}
