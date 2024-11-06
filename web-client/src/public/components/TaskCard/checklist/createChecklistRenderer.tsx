import { Remarkable } from 'remarkable'

import styles from '../../RichText/RichText.css';

type TConfig = {
  renderCheck: (listApiName: string, itemApiName: string) => string;
  renderProgressbar?: (listApiName: string) => string;
  interactiveChecklist?: boolean;
}

export const createChecklistRenderer = (config: TConfig) => (md: Remarkable) => {
  // eslint-disable-next-line no-param-reassign
  md.renderer.rules.clist_open = (tokens, idx) => {
    const isFirst = tokens[idx - 1]?.type !== 'clist_close';

    // @ts-ignore
    const listApiName = tokens[idx]['listApiName'] as string;
    // @ts-ignore
    const itemApiName = tokens[idx]['itemApiName'] as string;

    const checkbox = config.renderCheck(listApiName, itemApiName);
    const progressbar = config.renderProgressbar?.(listApiName) ;

    const checklistWrapperClass = `${styles['checklist']} ${config.interactiveChecklist ? styles['checklist_interactive'] : ''}`;
    let resultStr = '';
    resultStr += isFirst ? `<div class="${checklistWrapperClass}">` : '';
    resultStr += isFirst && progressbar ? `<div class="${styles['progressbar-container']}">${progressbar}</div>` : '';
    resultStr += `<div class="${styles['checkbox-wrapper']}">`;
    resultStr += checkbox;
    resultStr += `<span class="${styles['checkbox-content']}">`;

    return resultStr;
  }

  // eslint-disable-next-line no-param-reassign
  md.renderer.rules.clist_close = (tokens, idx) => {
    const isLast = tokens[idx + 1]?.type !== 'clist_open';
    const wrapper = isLast ? '</div>' : '';

    return `<span></div>${wrapper}`;
  }
}
