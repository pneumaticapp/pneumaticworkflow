export interface IMarkdownToken {
  type: string;
  tag: string;
  attrs: [string, string][] | null;
  map: null;
  nesting: number;
  level: number;
  children: IMarkdownToken[] | null;
  content: string;
  marks: string;
  info: string;
  meta: Record<string, unknown> | null;
  block: boolean;
  hidden: boolean;
}

export const createMarkdownToken = (
  type: string,
  tag: string,
  nesting: number,
): IMarkdownToken => ({
  type,
  tag,
  attrs: null,
  map: null,
  nesting,
  level: 0,
  children: null,
  content: '',
  marks: '',
  info: '',
  meta: null,
  block: false,
  hidden: false,
});
