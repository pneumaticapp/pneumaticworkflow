import { commonRequest } from './commonRequest';
import { IIntegrationDetailed } from '../types/integrations';
import { getBrowserConfigEnv } from '../utils/getConfig';

export type TGetIntegrationDetailsResponse = IIntegrationDetailed;

export function getIntegrationDetails(id: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.integrationDetails.replace(':id', String(id));

  return commonRequest<TGetIntegrationDetailsResponse>(
    url,
    {},
    { shouldThrow: true },
  );
}
