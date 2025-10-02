import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { TTemplateIntegrationStatsApi } from '../types/template';

type TGetTemplatesIntegrationsStatsConfig = {
  templates: number[];
};
export function getTemplatesIntegrationsStats({ templates }: TGetTemplatesIntegrationsStatsConfig) {
  const { api: { urls } } = getBrowserConfigEnv();

  const url = `${urls.templatesIntegrationsStats  }?template_id=${templates.join(',')}`;

  return commonRequest<TTemplateIntegrationStatsApi[]>(
    url,
    {
      method: 'GET',
    },
    {
      shouldThrow: true,
    },
  );
}
