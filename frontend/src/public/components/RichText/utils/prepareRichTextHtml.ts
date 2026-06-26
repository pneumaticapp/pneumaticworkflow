import * as xssFilters from 'xss-filters';
import { IntlShape } from 'react-intl';

import {
  mentionsRegex,
  variableRegex,
} from '../../../constants/defaultValues';
import { isArrayWithItems } from '../../../utils/helpers';
import { truncateString } from '../../../utils/truncateString';
import { prepareChecklistsForRendering } from '../../../utils/checklists/prepareChecklistsForRendering';
import { TTaskVariable } from '../../TemplateEdit/types';
import { getLocalizedSystemVariable } from '../../TemplateEdit/TaskForm/utils/getTaskVariables';

const MAX_VARIABLE_LENGTH = 20;

interface IPrepareRichTextHtmlOptions {
  variables?: TTaskVariable[];
  formatMessage: IntlShape['formatMessage'];
  mentionClassName: string;
  badgeClassName: string;
  specificityBadgeClassName: string;
}

type TReplaceRule =
  | { regExp: RegExp; replaceLogic: string }
  | { regExp: RegExp; replaceLogic: (substring: string, ...args: unknown[]) => string };

export function prepareRichTextHtml(
  text: string,
  {
    variables,
    formatMessage,
    mentionClassName,
    badgeClassName,
    specificityBadgeClassName,
  }: IPrepareRichTextHtmlOptions,
): string {
  const replaceRules: TReplaceRule[] = [
    {
      regExp: mentionsRegex,
      replaceLogic: `<span class='${mentionClassName}'>@$1</span>`,
    },
    {
      regExp: variableRegex,
      replaceLogic: (match: string, variableApiName: string) => {
        if (!isArrayWithItems(variables)) {
          return match;
        }

        const variable = variables.find((item) => variableApiName === item.apiName);
        if (!variable) {
          return match;
        }

        const { title } = getLocalizedSystemVariable({
          apiName: variableApiName,
          title: variable.title,
          formatMessage,
        });

        return `<span class="${badgeClassName} ${specificityBadgeClassName}">${truncateString(
          title,
          MAX_VARIABLE_LENGTH,
        )}</span>`;
      },
    },
  ];

  const sanitizedText = xssFilters.inHTMLData(prepareChecklistsForRendering(text));

  return replaceRules.reduce((acc, { regExp, replaceLogic }) => {
    const replaceRegex = new RegExp(regExp, 'gi');

    if (typeof replaceLogic === 'string') {
      return acc.replace(replaceRegex, replaceLogic);
    }

    return acc.replace(replaceRegex, replaceLogic);
  }, sanitizedText);
}
