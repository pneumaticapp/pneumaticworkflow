import type { ReactNode, MutableRefObject } from 'react';
import type { EditorState, LexicalEditor } from 'lexical';

import type { TOutputChecklist } from '../../../../types/template';
import type { TTaskVariable } from '../../../TemplateEdit/types';
import type { TForegroundColor } from '../../../UI/Fields/common/types';



export interface ILexicalRichEditorHandle {
  focus(): void;
  insertVariable(apiName: string, variableTitle: string, subtitle: string): void;
  getEditor?(): LexicalEditor | undefined;
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
  placeholder?: string;
  className?: string;
  defaultValue?: string;
  withMentions?: boolean;
  withToolbar?: boolean;
  withChecklists?: boolean;
  multiline?: boolean;
  children?: ReactNode;
  title?: string;
  foregroundColor?: TForegroundColor;
  stripPastedFormatting?: boolean;
  templateVariables?: TTaskVariable[];
  submitIcon?: ReactNode;
  cancelIcon?: ReactNode;
  isInTaskDescriptionEditor?: boolean;
  handleChange(value: string): Promise<string>;
  handleChangeChecklists?(checklists: TOutputChecklist[]): void;
  onUploadAttachments?(e: React.ChangeEvent<HTMLInputElement>): Promise<void>;
  onSubmit?(): void;
  onCancel?(): void;
}

export interface ILexicalEditorContentProps {
  placeholder?: string;
  withChecklists?: boolean;
  multiline: boolean;
  withToolbar: boolean;
  withMentions: boolean;
  mentions: TMentionData[] | undefined;
  isModal: boolean | undefined;
  onUploadAttachments?: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
  editorRef: MutableRefObject<LexicalEditor | null>;
  editorContainerRef?: React.RefObject<HTMLDivElement | null>;
  onChange: (editorState: EditorState) => void;
}
