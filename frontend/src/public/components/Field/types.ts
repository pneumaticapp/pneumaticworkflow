import type { ChangeEvent, KeyboardEvent, ReactNode } from 'react';

type NativeInputProps = Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  'onChange' | 'value'
>;

export interface IFieldProps extends NativeInputProps {
  labelClassName?: string;
  labelReplacementClassName?: string;
  labelReplacementValue?: string;
  icon?: ReactNode;
  intlId?: string;
  tagName?: EFieldTagName;
  shouldReplaceWithLabel?: boolean;
  onChange(e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void;
  validate?(value: string | number | string[] | undefined): string;
  errorMessage?: string;
  accountId?: number;
  onKeyDown?(event: KeyboardEvent<HTMLInputElement>): void;
  isNumericField?: boolean;
  isFromConditionValueField?: boolean;
  value?: string | number | string[];
  innerRef?: React.Ref<HTMLInputElement>;
}

export enum EFieldTagName {
  Input = 'input',
  Textarea = 'textarea',
  RichText = 'RichText',
}
