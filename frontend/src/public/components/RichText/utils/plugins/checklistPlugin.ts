import type MarkdownIt from 'markdown-it';

import styles from '../../RichText.css';

interface IChecklistBlockState {
  bMarks: number[];
  eMarks: number[];
  tShift: number[];
  src: string;
}

interface IChecklistPluginOptions {
  interactiveChecklists?: boolean;
  renderCheckPlaceholder: (listApiName: string, itemApiName: string) => string;
  renderProgressbarPlaceholder: (listApiName: string) => string;
}

const CLIST_START_RE = /^\[clist:([\w-]+)\|([\w-]+)\]/;
const CLIST_END_RE = /\[\/clist\]/;

const getLineText = (state: IChecklistBlockState, line: number): string => {
  const pos = state.bMarks[line] + state.tShift[line];
  const max = state.eMarks[line];

  return state.src.slice(pos, max);
};

export const checklistPlugin = (
  md: MarkdownIt,
  {
    interactiveChecklists,
    renderCheckPlaceholder,
    renderProgressbarPlaceholder,
  }: IChecklistPluginOptions,
): void => {
  md.block.ruler.before('paragraph', 'pneumatic_checklist', (state, startLine, endLine, silent) => {
    const blockState = state as IChecklistBlockState;
    const lineText = getLineText(blockState, startLine);
    const match = CLIST_START_RE.exec(lineText);

    if (!match) {
      return false;
    }

    if (silent) {
      return true;
    }

    const [, listApiName, itemApiName] = match;

    let currentLine = startLine;
    let totalLabelContent = '';

    while (currentLine < endLine) {
      const currentLineText = getLineText(blockState, currentLine);
      const blockEndMatch = CLIST_END_RE.exec(currentLineText);
      const currentContentStart = currentLine === startLine ? match[0].length : 0;
      const currentContentEnd = blockEndMatch ? blockEndMatch.index ?? currentLineText.length : currentLineText.length;

      totalLabelContent += currentLineText.slice(currentContentStart, currentContentEnd);

      if (blockEndMatch) {
        break;
      }

      currentLine += 1;
    }

    const tokenOpen = state.push('pneumatic_checklist_open', '', 1);
    tokenOpen.meta = { listApiName, itemApiName };
    tokenOpen.map = [startLine, currentLine + 1];

    const tokenInline = state.push('inline', '', 0);
    tokenInline.content = totalLabelContent;
    tokenInline.children = [];

    state.push('pneumatic_checklist_close', '', -1);

    state.line = currentLine + 1;

    return true;
  });

  md.renderer.rules.pneumatic_checklist_open = (tokens, idx) => {
    const isFirst = tokens[idx - 1]?.type !== 'pneumatic_checklist_close';
    const { listApiName, itemApiName } = tokens[idx].meta as {
      listApiName: string;
      itemApiName: string;
    };

    const checkbox = renderCheckPlaceholder(listApiName, itemApiName);
    const progressbar = renderProgressbarPlaceholder(listApiName);

    const checklistWrapperClass = `${styles['checklist']} ${interactiveChecklists ? styles['is-interactive'] : ''}`;

    let result = '';

    if (isFirst) {
      result += `<div class="${checklistWrapperClass}">`;
    }

    if (isFirst && progressbar) {
      result += `<div class="${styles['progressbar__container']}">${progressbar}</div>`;
    }

    result += `<div class="${styles['checklist__item']}">`;
    result += checkbox;
    result += `<span class="${styles['checklist__content']}">`;

    return result;
  };

  md.renderer.rules.pneumatic_checklist_close = (tokens, idx) => {
    const isLast = tokens[idx + 1]?.type !== 'pneumatic_checklist_open';
    const wrapper = isLast ? '</div>' : '';

    return `</span></div>${wrapper}`;
  };
};
