/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';

import { sanitizeText } from '../../utils/strings';

interface ITemplateNameProps extends React.HTMLAttributes<HTMLSpanElement> {
  isLegacyTemplate: boolean;
  legacyTemplateName: string;
  templateName?: string;
}

export const TemplateName = ({ isLegacyTemplate, legacyTemplateName, templateName, ...rest }: ITemplateNameProps) => {
  if (isLegacyTemplate) {
    const { formatMessage } = useIntl();
    const postfix = formatMessage({ id: 'legacy-template' });
    const result = legacyTemplateName ? `${sanitizeText(legacyTemplateName)} ${postfix}` : postfix;

    return (
      <span {...rest}>
        {result}
      </span>
    );
  }

  if (templateName) {
    return (
      <span {...rest}>
        {sanitizeText(templateName)}
      </span>
    );
  }

  return null;
};
