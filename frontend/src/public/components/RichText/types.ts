import type { TTaskVariable } from '../../types/template';

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
