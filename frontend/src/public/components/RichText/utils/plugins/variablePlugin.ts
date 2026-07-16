import type MarkdownIt from 'markdown-it';
import { IntlShape } from 'react-intl';

import { variableRegex } from '../../../../constants/defaultValues';
import { isArrayWithItems } from '../../../../utils/helpers';
import { truncateString } from '../../../../utils/truncateString';
import { TTaskVariable } from '../../../TemplateEdit/types';
import { getLocalizedSystemVariable } from '../../../TemplateEdit/TaskForm/utils/getTaskVariables';

const MAX_VARIABLE_LENGTH = 20;

interface IVariablePluginOptions {
  variables?: TTaskVariable[];
  formatMessage: IntlShape['formatMessage'];
  badgeClassName: string;
  specificityBadgeClassName: string;
}

const VARIABLE_INLINE_RE = new RegExp(`^${variableRegex.source}`, variableRegex.flags);

export const variablePlugin = (
  md: MarkdownIt,
  {
    variables,
    formatMessage,
    badgeClassName,
    specificityBadgeClassName,
  }: IVariablePluginOptions,
): void => {
  md.inline.ruler.before('link', 'pneumatic_variable', (state, silent) => {
    const match = VARIABLE_INLINE_RE.exec(state.src.slice(state.pos));

    if (!match) {
      return false;
    }

    const variableApiName = match[1];

    if (!isArrayWithItems(variables)) {
      return false;
    }

    const variable = variables.find((item) => variableApiName === item.apiName);

    if (!variable) {
      return false;
    }

    if (!silent) {
      const { title } = getLocalizedSystemVariable({
        apiName: variableApiName,
        title: variable.title,
        formatMessage,
      });

      const token = state.push('pneumatic_variable', '', 0);
      token.content = truncateString(title ?? variableApiName, MAX_VARIABLE_LENGTH) ?? variableApiName;
      token.meta = { badgeClassName, specificityBadgeClassName };
    }

    state.pos += match[0].length;

    return true;
  });

  md.renderer.rules.pneumatic_variable = (tokens, idx) => {
    const token = tokens[idx];
    const {
      badgeClassName: variableBadgeClassName,
      specificityBadgeClassName: variableSpecificityBadgeClassName,
    } = token.meta as {
      badgeClassName: string;
      specificityBadgeClassName: string;
    };

    return `<span class="${variableBadgeClassName} ${variableSpecificityBadgeClassName}">${md.utils.escapeHtml(token.content)}</span>`;
  };
};
