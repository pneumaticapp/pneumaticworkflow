import type { HTMLProps } from 'react';

export interface ITextareaFieldProps {
  title?: string;
  errorMessage?: string;
  isRequired?: boolean;
}

export type TTextareaFieldProps = ITextareaFieldProps & HTMLProps<HTMLTextAreaElement>;
