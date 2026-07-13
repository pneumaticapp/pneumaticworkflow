import { EIntegrations } from '../../../types/integrations';
import { isArrayWithItems } from '../../../utils/helpers';

// Webhooks are excluded from the template card integration badge only.
// Draft warnings and edit controls still treat webhooks as external access.
export const TEMPLATE_CARD_INTEGRATIONS_EXCLUDE = [EIntegrations.Webhooks];

export function hasTemplateIntegrations(
  isTemplatePublic: boolean,
  templateIntegrations: EIntegrations[],
) {
  return isTemplatePublic || isArrayWithItems(templateIntegrations);
}
