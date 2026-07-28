import { EIntegrations } from '../../../types/integrations';

// Webhooks are account-wide, so they do not affect a template card's state.
export const TEMPLATE_CARD_INTEGRATIONS_EXCLUDE = [EIntegrations.Webhooks];

export function hasTemplateCardIntegrations(templateIntegrations: EIntegrations[]) {
  return templateIntegrations.some(
    integration => !TEMPLATE_CARD_INTEGRATIONS_EXCLUDE.includes(integration),
  );
}
