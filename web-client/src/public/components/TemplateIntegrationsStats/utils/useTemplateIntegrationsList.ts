import { useSelector } from 'react-redux';
import { getTemplatesIntegrationsStats } from '../../../redux/selectors/templates';
import { EIntegrations } from '../../../types/integrations';

export const useTemplateIntegrationsList = (templateId?: number, exlcudedIntegrations?: EIntegrations[]): EIntegrations[] => {
  const templatesIntegrationsStats = useSelector(getTemplatesIntegrationsStats);
  if (!templateId) {
    return [];
  }

  const stats = templatesIntegrationsStats[templateId];
  if (!stats) {
    return [];
  }

  return Object.entries(stats)
    .filter(([, isConnected]) => isConnected)
    .map(([integration]) => integration as EIntegrations)
    .filter(i => !exlcudedIntegrations?.includes(i));
};
