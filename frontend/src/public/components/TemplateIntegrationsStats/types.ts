import type { ReactNode } from 'react';
import type { EIntegrations } from '../../types/integrations';

export interface ITemplateIntegrationsStatsProps {
  templateId?: number;
  exlcude?: EIntegrations[];
  children(integrations: EIntegrations[]): ReactNode;
}

export interface ITemplateIntegrationsIndicatorProps extends Pick<
  ITemplateIntegrationsStatsProps,
  'templateId' | 'exlcude'
> {
  integratedIndicator: JSX.Element;
  disconnectedIndicator: JSX.Element;
}
