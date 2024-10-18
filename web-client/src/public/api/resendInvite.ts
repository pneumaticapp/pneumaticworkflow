import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';
import { getBrowserConfigEnv } from '../utils/getConfig';

export function resendInvite(inviteId: number) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest(
    urls.resendInvite.replace(':id', String(inviteId)), {
      method: 'POST',
      body: mapRequestBody({ inviteId }),
      headers: { 'Content-Type': 'application/json' },
    }, {
      type: 'local', shouldThrow: true, responseType: 'empty',
    });
}
