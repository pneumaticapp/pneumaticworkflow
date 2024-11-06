/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import { Input, InputProps } from 'reactstrap';

import { IntlMessages } from '../IntlMessages';
import { onEnterPressed } from '../../utils/handlers';

import { RichEditorContainer } from '../RichEditor';
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
      };

      const input = (
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
      <RichEditorContainer
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

  private setTouched = () => this.setState({ touched: true });
}
