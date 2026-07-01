import { TTaskVariable } from '../TemplateEdit/types';

export interface IRichTextProps {
    text: string | null;
    isMarkdownMode?: boolean;
    embedVideos?: boolean;
    variables?: TTaskVariable[];
    renderExtensions?: React.ReactNode[];
    interactiveChecklists?: boolean;
    hideIcon?: boolean;
    maxLines?: number;
    className?: string;
  }
  