import type { TTaskVariable } from '../../../TemplateEdit/types';

export type TConvertLexicalToMarkdownOptions = {
  preserveNewlines?: boolean;
};

export type TGetInitialLexicalStateParams = {
  markdown: string;
  templateVariables?: TTaskVariable[];
};
