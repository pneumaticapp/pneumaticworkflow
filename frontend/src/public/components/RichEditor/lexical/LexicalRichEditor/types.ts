import type { ReactNode } from 'react';
import type { LexicalEditor } from 'lexical';
import type { TOutputChecklist } from '../../../../types/template';
import type { TTaskVariable } from '../../../TemplateEdit/types';

export interface ILexicalRichEditorHandle {
  focus(): void;
  insertVariable(apiName?: string, title?: string, subtitle?: string | ReactNode): void;
  getEditor?(): LexicalEditor;
}

export type TMentionData = {
  id?: number;
  name: string;
  link?: string;
};

export interface ILexicalRichEditorProps {
  isModal?: boolean;
  accountId?: number;
  mentions?: TMentionData[];
  placeholder: string;
  className?: string;
  defaultValue?: string;
  withMentions?: boolean;
  withToolbar?: boolean;
  withChecklists?: boolean;
  multiline?: boolean;
  children?: ReactNode;
  title?: string;
  foregroundColor?: string;
  stripPastedFormatting?: boolean;
  templateVariables?: TTaskVariable[];
  submitIcon?: ReactNode;
  cancelIcon?: ReactNode;
  isInTaskDescriptionEditor?: boolean;
  handleChange(value: string): Promise<string>;
  handleChangeChecklists?(checklists: TOutputChecklist[]): void;
  onSubmit?(): void;
  onCancel?(): void;
}
