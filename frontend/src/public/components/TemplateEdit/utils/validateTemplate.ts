/* eslint-disable */
/* prettier-ignore */
import { IntlShape } from 'react-intl';

import { ITemplate } from '../../../types/template';
import { IInfoWarningProps } from '../InfoWarningsModal/warnings';
import { collectTemplateValidationErrors } from '../templateValidation/collectTemplateValidationErrors';

/**
 * @deprecated Prefer `collectTemplateValidationErrors` for field-level errors.
 * Kept for callers that still expect formatted toast strings.
 */
export function validateTemplate(template: ITemplate, isSubscribed: boolean, intl: IntlShape) {
  const { formatMessage } = intl;
  const { blockingErrors, infoWarnings } = collectTemplateValidationErrors(template, isSubscribed);

  return {
    blockingErrors,
    infoWarnings,
    commonWarnings: blockingErrors.map(({ messageId }) => formatMessage({ id: messageId })),
  };
}

export type { IInfoWarningProps };
