import type { ChangeEvent, ClipboardEvent, FocusEvent, KeyboardEvent, ReactNode, Ref } from 'react';

type TInputAttrsOmit =
  | 'value'
  | 'onChange'
  | 'type'
  | 'placeholder'
  | 'disabled'
  | 'ref'
  | 'onBlur'
  | 'onKeyDown'
  | 'onPaste'
  | 'className'
  | 'style';

export type TFieldInputRest = Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  TInputAttrsOmit
>;

/** Rest props safe to spread onto NumericFormat (defaultValue excluded for type compatibility). */
export type TNumericFormatRest = Omit<TFieldInputRest, 'defaultValue'>;

export interface IFieldInputProps {
  inputClassName: string;
  value: string | number | string[] | undefined;
  onChange(e: ChangeEvent<HTMLInputElement>): void;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
  innerRef?: Ref<HTMLInputElement>;
  shouldReplaceWithLabel?: boolean;
  isFromConditionValueField?: boolean;
  isNumericField?: boolean;
  onBlur?(e: FocusEvent<HTMLInputElement>): void;
  onKeyDown?(e: KeyboardEvent<HTMLInputElement>): void;
  onPaste?(e: ClipboardEvent): void;
  icon?: ReactNode;
  labelReplacementClassName?: string;
  labelReplacementValue?: string;
  rest: TFieldInputRest;
}
