import * as React from 'react';
import { EIntegrations } from '../../types/integrations';
import { useTemplateIntegrationsList } from './utils/useTemplateIntegrationsList';

export interface ITemplateIntegrationsStatsProps {
  templateId?: number;
  exlcude?: EIntegrations[];
  
  children(integrations: EIntegrations[]): React.ReactNode;
}

export const TemplateIntegrationsStats = ({
  templateId,
  exlcude,
  children,
}: ITemplateIntegrationsStatsProps) => {
  if (!templateId) {
    return <>{children([])}</>;
  }

  const connectedIntegrations = useTemplateIntegrationsList(templateId, exlcude);

  return <>{children(connectedIntegrations)}</>;
};
