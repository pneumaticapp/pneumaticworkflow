import { EIntegrations } from '../../../types/integrations';

import { hasTemplateIntegrations } from './templateIntegrations';

export function checkShowDraftTemplateWarning(
  isTemplateActive: boolean,
  isTemplatePublic: boolean,
  templateIntegrations: EIntegrations[],
) {
  return !isTemplateActive && hasTemplateIntegrations(isTemplatePublic, templateIntegrations);
}
