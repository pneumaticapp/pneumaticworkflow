import { EIntegrations } from '../../../types/integrations';
import { isArrayWithItems } from '../../../utils/helpers';

export const TEMPLATE_CARD_INTEGRATIONS_EXCLUDE = [EIntegrations.Webhooks];

export function hasTemplateIntegrations(
  isTemplatePublic: boolean,
  templateIntegrations: EIntegrations[],
) {
  return isTemplatePublic || isArrayWithItems(templateIntegrations);
}
