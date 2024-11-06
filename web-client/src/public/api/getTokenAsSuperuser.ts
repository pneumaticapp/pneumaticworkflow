import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface IGetTokenAsSuperuserResponse {
  token: string;
}

export function getTokenAsSuperuser(email: string) {
  const { api: { urls } } = getBrowserConfigEnv();
  const url = urls.superuserToken;

  return commonRequest<IGetTokenAsSuperuserResponse>(url, {
    method: 'POST',
    body: mapRequestBody({ email }),
  }, {
    type: 'local',
    shouldThrow: true,
  });
}
