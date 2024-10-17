import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';

export function declineInvite(inviteId: string) {
  return commonRequest('declineInvite', {
    method: 'POST',
    body: mapRequestBody({ inviteId }),
    headers: { 'Content-Type': 'application/json' },
  }, {
    type: 'local', shouldThrow: true, responseType: 'empty',
  });
}
