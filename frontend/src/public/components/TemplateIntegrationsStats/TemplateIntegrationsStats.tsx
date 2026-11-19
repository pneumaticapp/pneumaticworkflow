import React from 'react';
import type { ITemplateIntegrationsStatsProps } from './types';
import { useTemplateIntegrationsList } from './utils/useTemplateIntegrationsList';

export const TemplateIntegrationsStats = ({ templateId, exlcude, children }: ITemplateIntegrationsStatsProps) => {
  if (!templateId) {
    return <>{children([])}</>;
  }

  const connectedIntegrations = useTemplateIntegrationsList(templateId, exlcude);

  return <>{children(connectedIntegrations)}</>;
};
